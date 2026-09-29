"""
VERITAS AI — Real Temporal Forensic Detector
Module: backend.app.models.temporal_detector

Provides the Real Temporal Forensic Stability Detector using measurable statistical
and physical stability features across tracked facial subjects.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from pathlib import Path
import logging

from app.services.video_forensics import (
    video_forensic_engine,
    RealVideoForensicEngine,
    TemporalForensicAnalyzer,
    TEMPORAL_LIMITATIONS,
    VideoSamplingConfig
)
from app.services.media_processor import temporary_media_workspace

logger = logging.getLogger("veritas.models.temporal")

TEMPORAL_FORMULA_DOCS = (
    "Temporal Anomaly Score = round(100 * ( "
    "0.40 * min(1.0, 2*Score_Std) + "
    "0.25 * min(1.0, 5*Normalized_BBox_Displacement) + "
    "0.20 * min(1.0, 5*Normalized_Landmark_Jitter) + "
    "0.15 * (1.0 - Consecutive_Detection_Ratio) ))"
)


class TemporalDetector(ABC):
    """Abstract base detector interface for inter-frame motion consistency."""
    
    @abstractmethod
    def analyze(self, media_path_or_bytes: Any) -> Dict[str, Any]:
        pass


class MockTemporalDetector(TemporalDetector):
    """
    Simulated demo detector for temporal consistency.
    Explicitly labeled as DEMO MODE // SIMULATED TEMPORAL DETECTION.
    """
    def __init__(self, model_version: str = "VERITAS-TEMPORAL-MOCK-v0.1"):
        self.model_version = model_version
        self.is_mock = True
        self.detection_mode = "DEMO MODE // SIMULATED TEMPORAL DETECTION"

    def analyze(self, media_path_or_bytes: Any) -> Dict[str, Any]:
        return {
            "model_name": "Video-Swin-3D Temporal Consistency Net (Simulated)",
            "model_version": self.model_version,
            "category": "Temporal AI",
            "evidence_source": "TEMPORAL",
            "detection_mode": self.detection_mode,
            "is_mock": True,
            "classification_status": "ANALYZED",
            "score": 84,
            "confidence": 89,
            "temporal_anomaly_score": 84,
            "signals": [
                {
                    "id": "sig-tmp-mock-1",
                    "name": "Optical-Flow Inter-Frame Anomaly (Simulated)",
                    "category": "temporal",
                    "evidence_source": "TEMPORAL",
                    "severity": "high",
                    "confidence": 89,
                    "affectedRegionOrTime": "Frames #420-#480 [00:14 - 00:16]",
                    "explanation": "Vector motion fields around facial contours misalign with background optical flow velocity."
                }
            ],
            "formula_documentation": "Simulated demonstration heuristic",
            "limitations": TEMPORAL_LIMITATIONS,
            "latency_ms": 44
        }


class RealTemporalDetector(TemporalDetector):
    """
    Real Temporal Forensic Detector:
    Extracts measurable temporal features across video frames / face tracks
    (variance, inter-frame residual jumps, landmark jitter, bbox stability, and continuity)
    to compute the Temporal Anomaly Score.
    
    NOTE: This is a mathematical temporal anomaly score based on measurable stability,
    not a deep 3D-CNN trained temporal model.
    """
    def __init__(
        self,
        engine: Optional[RealVideoForensicEngine] = None,
        sampling_config: Optional[VideoSamplingConfig] = None
    ):
        self.engine = engine or video_forensic_engine
        self.sampling_config = sampling_config or VideoSamplingConfig()
        self.model_version = "VERITAS-TEMPORAL-REAL-v1.0"
        self.is_mock = False
        self.detection_mode = "REAL_AI_TEMPORAL"
        self._mock_fallback = MockTemporalDetector()

    def analyze(self, media_path_or_bytes: Any) -> Dict[str, Any]:
        # 1. Path or String Path
        if isinstance(media_path_or_bytes, (str, Path)):
            p = Path(media_path_or_bytes)
            if p.exists() and p.is_file():
                raw = self.engine.analyze_video(p, sampling_config=self.sampling_config)
                return self._format_temporal_response(raw)
            else:
                logger.warning(
                    f"Video file not found at '{media_path_or_bytes}'. "
                    f"Falling back to MockTemporalDetector."
                )
                return self._mock_fallback.analyze(media_path_or_bytes)

        # 2. Raw Bytes Ingestion
        elif isinstance(media_path_or_bytes, bytes):
            with temporary_media_workspace() as tmp_dir:
                tmp_file = tmp_dir / "input_video.mp4"
                tmp_file.write_bytes(media_path_or_bytes)
                raw = self.engine.analyze_video(tmp_file, sampling_config=self.sampling_config)
                return self._format_temporal_response(raw)

        else:
            logger.warning(
                f"Unsupported video input type '{type(media_path_or_bytes)}'. "
                f"Falling back to MockTemporalDetector."
            )
            return self._mock_fallback.analyze(media_path_or_bytes)

    def _format_temporal_response(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        status = raw_result.get("classification_status", "ANALYZED")
        if status == "INSUFFICIENT_FACE_EVIDENCE":
            return {
                "model_name": "Temporal Stability & Landmark Motion Consistency Engine",
                "model_version": self.model_version,
                "category": "Temporal AI",
                "evidence_source": "TEMPORAL",
                "detection_mode": self.detection_mode,
                "is_mock": False,
                "classification_status": "INSUFFICIENT_FACE_EVIDENCE",
                "score": 0,
                "confidence": 0,
                "temporal_anomaly_score": None,
                "signals": [],
                "formula_documentation": TEMPORAL_FORMULA_DOCS,
                "limitations": TEMPORAL_LIMITATIONS,
                "latency_ms": raw_result.get("performance", {}).get("temporal_analysis_ms", 0.0)
            }

        temporal_score = raw_result.get("temporal_anomaly_score") or 0
        temporal_signals = [
            sig for sig in raw_result.get("signals", [])
            if sig.get("category") == "temporal"
        ]

        conf = 88 if status in ("ANALYZED", "ANALYZED_GENERAL_VIDEO") else 0

        return {
            "model_name": "Temporal Stability & Landmark Motion Consistency Engine",
            "model_version": self.model_version,
            "category": "Temporal AI",
            "evidence_source": "TEMPORAL",
            "detection_mode": self.detection_mode,
            "is_mock": False,
            "classification_status": status,
            "score": temporal_score,
            "confidence": conf,
            "temporal_anomaly_score": temporal_score,
            "signals": temporal_signals,
            "formula_documentation": TEMPORAL_FORMULA_DOCS,
            "limitations": TEMPORAL_LIMITATIONS,
            "latency_ms": raw_result.get("performance", {}).get("temporal_analysis_ms", 0.0)
        }


def get_temporal_detector(force_mock: bool = False) -> TemporalDetector:
    """Factory creating the appropriate temporal detector."""
    if force_mock:
        return MockTemporalDetector()
    try:
        return RealTemporalDetector()
    except Exception as exc:
        logger.error(f"Failed to initialize RealTemporalDetector: {exc}. Falling back to MockTemporalDetector.")
        return MockTemporalDetector()
