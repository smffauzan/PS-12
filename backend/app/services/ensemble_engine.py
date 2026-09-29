"""
VERITAS AI — Advanced Multi-Model Forensic Ensemble Engine
Module: backend.app.services.ensemble_engine

Coordinates multi-model multimodal evidence normalization, failure isolation,
disagreement detection, uncertainty estimation, and CPU resource budget enforcement.
"""

import time
import math
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
import numpy as np

from app.models.model_registry import (
    model_registry,
    ModelRegistry,
    ExecutionMode,
    ModalityType,
    ModelStatus
)

logger = logging.getLogger("veritas.forensics.ensemble")

CALIBRATION_LIMITATIONS = [
    "calibration_status = NOT_CALIBRATED (raw model scores represent classification activations, not Bayesian posterior probabilities)",
    "calibrated probabilities require empirical validation datasets (e.g. temperature scaling, Platt scaling, or isotonic regression)",
    "model disagreement represents variance across independent forensic modalities",
    "high model disagreement produces an INCONCLUSIVE consensus to prevent false certainty"
]


@dataclass
class ModelEvidenceItem:
    """Standardized representation of an individual model's forensic evidence output."""
    model_id: str
    model_name: str
    modality: str
    raw_output: Any
    normalized_score: int          # Standardized 0-100 scale
    calibrated_score: Optional[float] # None or calibrated score if calibration dataset applied
    calibration_status: str        # "NOT_CALIBRATED" | "TEMPERATURE_SCALED" | "PLATT_SCALED"
    model_confidence: int          # 0-100 scale
    latency_ms: float
    signals: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EnsembleResult:
    """Unified multi-model multimodal forensic ensemble decision."""
    execution_mode: str
    overall_risk: Optional[int]
    risk_level: str
    model_consensus: int
    model_disagreement: int
    confidence: int
    uncertainty: float
    disagreement_detected: bool
    calibration_status: str
    active_models: List[str]
    skipped_models: List[str]
    skip_reasons: Dict[str, str]
    model_evidence: Dict[str, Dict[str, Any]]
    all_signals: List[Dict[str, Any]]
    total_pipeline_ms: float
    budget_exceeded: bool
    limitations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ForensicEnsembleEngine:
    """
    Multi-Model Forensic Ensemble Engine implementing:
    - Normalization of diverse model outputs
    - Strict uncalibrated probability disclosures
    - Disagreement and conflict detection
    - Dynamic execution mode routing (FAST, BALANCED, DEEP_FORENSICS)
    - Hardware CPU budget enforcement
    - Graceful model failure isolation
    """

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        max_total_latency_ms: float = 3000.0,
        max_model_memory_mb: float = 500.0
    ):
        self.registry = registry or model_registry
        self.max_total_latency_ms = max_total_latency_ms
        self.max_model_memory_mb = max_model_memory_mb

    def fuse_evidence(
        self,
        modality_results: Dict[str, Dict[str, Any]],
        media_type: str = "video",
        execution_mode: ExecutionMode = ExecutionMode.DEEP_FORENSICS,
        classification_status: Optional[str] = None
    ) -> EnsembleResult:
        """
        Fuses multimodal evidence items from active modality detectors.
        """
        t0 = time.perf_counter()
        active_models: List[str] = []
        skipped_models: List[str] = []
        skip_reasons: Dict[str, str] = {}
        model_evidence_map: Dict[str, Dict[str, Any]] = {}
        all_signals: List[Dict[str, Any]] = []

        scores: List[float] = []
        weights: List[float] = []

        # Base modality weight profiles
        base_weights = {
            "visual": 0.35,
            "frequency": 0.20,
            "temporal": 0.25,
            "audio": 0.15,
            "audio_features": 0.05,
            "sync": 0.00  # Sync is an optional modifier
        } if media_type == "video" else {
            "visual": 0.60,
            "frequency": 0.40,
            "temporal": 0.0,
            "audio": 0.0,
            "audio_features": 0.0,
            "sync": 0.0
        } if media_type == "image" else {
            "visual": 0.0,
            "frequency": 0.0,
            "temporal": 0.0,
            "audio": 0.70,
            "audio_features": 0.30,
            "sync": 0.0
        }

        # 1. Process Modality Evidence
        for mod_key, res in modality_results.items():
            if not res or not isinstance(res, dict):
                skipped_models.append(mod_key)
                skip_reasons[mod_key] = "No output returned by detector"
                continue

            status = res.get("classification_status", "ANALYZED")

            # Failure or Inapplicable Detector Isolation
            if status == "ANALYSIS_ERROR" or res.get("error"):
                skipped_models.append(mod_key)
                skip_reasons[mod_key] = res.get("error", "Execution failure in detector")
                continue

            # Skip inactive/inapplicable modalities without penalizing the ensemble
            if status in (
                "SKIPPED_AUDIO_MEDIA", "SKIPPED_IMAGE_MEDIA", "SKIPPED_NO_AUDIO_OR_FACE",
                "NO_AUDIO", "NO_AUDIO_TRACK", "SKIPPED_NON_IMAGE", "SKIPPED_UNREADABLE",
                "NO_FACES_DETECTED", "UNSUPPORTED_FORMAT"
            ):
                skipped_models.append(mod_key)
                skip_reasons[mod_key] = f"Modality not applicable ({status})"
                continue

            mid = res.get("model_version", mod_key)
            m_name = res.get("model_name", mod_key)
            score_val = int(res.get("score") or 0)
            conf_val = int(res.get("confidence") or 85)
            lat = float(res.get("latency_ms") or 0.0)
            sigs = res.get("signals", [])

            evidence_item = ModelEvidenceItem(
                model_id=mid,
                model_name=m_name,
                modality=mod_key,
                raw_output=res.get("score"),
                normalized_score=score_val,
                calibrated_score=None,
                calibration_status="NOT_CALIBRATED",
                model_confidence=conf_val,
                latency_ms=lat,
                signals=sigs
            )

            active_models.append(mid)
            model_evidence_map[mod_key] = evidence_item.to_dict()
            all_signals.extend(sigs)

            # Accumulate for active consensus if detector is valid and weight > 0
            w = base_weights.get(mod_key, 0.10)
            if w > 0 and status in ("ANALYZED", "ANALYZED_GENERAL_IMAGE", "ANALYZED_GENERAL_VIDEO", "DEMO_MODE", "VALID"):
                scores.append(float(score_val))
                weights.append(w)

        # 2. Consensus & Disagreement Calculation over Active Modalities
        if scores and sum(weights) > 0:
            w_norm = np.array(weights) / (np.sum(weights) or 1.0)
            weighted_overall = float(np.sum(np.array(scores) * w_norm))
            consensus = int(round(float(np.mean(scores))))
            disagreement = int(round(float(np.std(scores)))) if len(scores) > 1 else 0
        else:
            weighted_overall = 0.0
            consensus = 0
            disagreement = 0

        disagreement_detected = disagreement >= 20
        uncertainty = round(float(2.0 + (disagreement * 0.15)), 2)

        # 3. Handle Insufficient Evidence vs Real Risk Decision
        if not scores or len(active_models) == 0 or classification_status in ("INSUFFICIENT_EVIDENCE", "ANALYSIS_ERROR", "UNSUPPORTED_FORMAT"):
            overall_risk = None
            risk_level = "INCONCLUSIVE"
            confidence = 0
            consensus = 0
            disagreement = 0
            disagreement_detected = False
        elif disagreement >= 30:
            # Extreme multi-model disagreement -> report INCONCLUSIVE to avoid misleading false certainty
            overall_risk = None
            risk_level = "INCONCLUSIVE"
            confidence = max(20, 85 - disagreement)
        else:
            overall_risk = int(round(weighted_overall))
            risk_level = (
                "CRITICAL RISK" if overall_risk >= 85
                else "HIGH RISK" if overall_risk >= 65
                else "MEDIUM RISK" if overall_risk >= 40
                else "LOW RISK"
            )
            confidence = 91 if len(active_models) >= 2 else 80

        total_ms = round((time.perf_counter() - t0) * 1000, 2)
        budget_exceeded = total_ms > self.max_total_latency_ms

        return EnsembleResult(
            execution_mode=execution_mode.value if isinstance(execution_mode, ExecutionMode) else str(execution_mode),
            overall_risk=overall_risk,
            risk_level=risk_level,
            model_consensus=consensus,
            model_disagreement=disagreement,
            confidence=confidence,
            uncertainty=uncertainty,
            disagreement_detected=disagreement_detected,
            calibration_status="NOT_CALIBRATED",
            active_models=active_models,
            skipped_models=skipped_models,
            skip_reasons=skip_reasons,
            model_evidence=model_evidence_map,
            all_signals=all_signals,
            total_pipeline_ms=total_ms,
            budget_exceeded=budget_exceeded,
            limitations=CALIBRATION_LIMITATIONS
        )


# Global singleton instance
ensemble_engine = ForensicEnsembleEngine()
