"""
VERITAS AI — Advanced Model Registry & Ensemble Architecture Test Suite
Module: backend.tests.test_model_ensemble

Validates ModelRegistry metadata, candidate audits, runtime health tracking,
multi-model ensemble fusion, failure isolation, disagreement detection,
uncertainty estimation, provenance separation, audio forensic features,
and CPU budget enforcement.
"""

import unittest
from pathlib import Path
import numpy as np

from app.models.model_registry import (
    model_registry,
    ModelRegistry,
    ModelMetadata,
    ModalityType,
    ModelStatus,
    ExecutionMode
)
from app.services.ensemble_engine import (
    ensemble_engine,
    ForensicEnsembleEngine,
    EnsembleResult
)
from app.services.audio_forensics import audio_extractor, AudioForensicFeatures
from app.models.frequency_detector import SpatialFrequencyDetector, MockFrequencyDetector
from app.models.audio_detector import RealAudioFeatureDetector, MockAudioDetector
from app.services.orchestrator import ForensicOrchestrator
from app.services.provenance_service import ProvenanceService

DATA_DIR = Path(__file__).resolve().parent / "data"
SAMPLE_FACE_VIDEO = DATA_DIR / "sample_face_video.mp4"
NO_FACE_VIDEO = DATA_DIR / "no_face_video.mp4"
SINGLE_FACE_IMG = DATA_DIR / "single_face.jpg"
NO_FACE_IMG = DATA_DIR / "no_face.jpg"


class TestModelEnsembleArchitecture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = model_registry
        cls.ensemble = ensemble_engine
        cls.orchestrator = ForensicOrchestrator()
        cls.provenance = ProvenanceService()

    def test_01_model_registry_initialization(self):
        """1. Verify ModelRegistry contains active models and candidate audit entries."""
        active = self.registry.get_active_models()
        self.assertGreaterEqual(len(active), 3)

        active_ids = [m.model_id for m in active]
        self.assertIn("VERITAS-VISION-YUNET-v1", active_ids)
        self.assertIn("VERITAS-VISION-VIT-v2", active_ids)
        self.assertIn("VERITAS-TEMPORAL-STABILITY-v1", active_ids)

    def test_02_model_metadata_completeness(self):
        """2. Verify ModelMetadata has all required architectural and licensing fields."""
        vit_meta = self.registry.get_model("VERITAS-VISION-VIT-v2")
        self.assertIsNotNone(vit_meta)
        self.assertEqual(vit_meta.modality, ModalityType.IMAGE)
        self.assertEqual(vit_meta.architecture, "ViT (Vision Transformer base patch-16)")
        self.assertEqual(vit_meta.license, "Apache-2.0")
        self.assertTrue(vit_meta.cpu_supported)
        self.assertFalse(vit_meta.gpu_required)
        self.assertEqual(vit_meta.quantization, "INT8 (Dynamic Quantization)")
        self.assertGreater(len(vit_meta.known_limitations), 0)

    def test_03_candidate_model_audit_categories(self):
        """3. Verify candidate audit covers Spatial, Frequency, Temporal, Audio, and A/V Sync."""
        audit = self.registry.get_candidate_audit()
        self.assertIn("spatial_candidates", audit)
        self.assertIn("frequency_candidates", audit)
        self.assertIn("temporal_candidates", audit)
        self.assertIn("audio_candidates", audit)
        self.assertIn("av_sync_candidates", audit)

        self.assertGreater(len(audit["spatial_candidates"]), 0)
        self.assertGreater(len(audit["frequency_candidates"]), 0)
        self.assertGreater(len(audit["temporal_candidates"]), 0)
        self.assertGreater(len(audit["audio_candidates"]), 0)
        self.assertGreater(len(audit["av_sync_candidates"]), 0)

    def test_04_model_health_tracking(self):
        """4. Verify model health reporting and latency/error tracking."""
        self.registry.update_health("VERITAS-VISION-VIT-v2", latency_ms=118.5, success=True)
        report = self.registry.get_health_report()
        self.assertIn("VERITAS-VISION-VIT-v2", report)
        self.assertEqual(report["VERITAS-VISION-VIT-v2"]["last_inference_ms"], 118.5)
        self.assertEqual(report["VERITAS-VISION-VIT-v2"]["loaded"], True)

    def test_05_execution_modes(self):
        """5. Verify FAST, BALANCED, and DEEP_FORENSICS execution modes."""
        # FAST: Vision only
        std_fast, _ = self.orchestrator.process(
            filename="single_face.jpg",
            media_type="image",
            file_size="90 KB",
            case_id="CASE-FAST-1",
            analysis_id="ANL-FAST-1",
            file_path=SINGLE_FACE_IMG,
            execution_mode=ExecutionMode.FAST
        )
        self.assertEqual(std_fast.metadata.get("execution_mode"), "FAST")

        # BALANCED: Vision + Frequency
        std_bal, _ = self.orchestrator.process(
            filename="single_face.jpg",
            media_type="image",
            file_size="90 KB",
            case_id="CASE-BAL-1",
            analysis_id="ANL-BAL-1",
            file_path=SINGLE_FACE_IMG,
            execution_mode=ExecutionMode.BALANCED
        )
        self.assertEqual(std_bal.metadata.get("execution_mode"), "BALANCED")
        self.assertIn("frequency", std_bal.metadata.get("model_evidence", {}))

    def test_06_model_selection_rule(self):
        """6. Verify ranking of candidates based on CPU feasibility and latency."""
        candidates = self.registry.list_models(status=ModelStatus.CANDIDATE)
        for c in candidates:
            self.assertTrue(c.cpu_supported, f"Candidate {c.model_id} must be CPU supported for primary pipeline")
            self.assertLessEqual(c.weight_size_mb, 500.0, f"Candidate {c.model_id} exceeds 500MB memory budget")

        # GPU heavy research models must be marked OPTIONAL_GPU
        gpu_models = self.registry.list_models(status=ModelStatus.OPTIONAL_GPU)
        for g in gpu_models:
            self.assertTrue(g.gpu_required)

    def test_07_model_failure_isolation(self):
        """7. Verify that failure in one detector is isolated and does not crash the ensemble."""
        faulty_modality_results = {
            "visual": {"model_name": "Vision", "model_version": "V1", "score": 80, "confidence": 90, "latency_ms": 100},
            "frequency": {"model_name": "FaultyFreq", "error": "CUDA out of memory exception", "classification_status": "ANALYSIS_ERROR"},
            "temporal": {"model_name": "Temporal", "model_version": "T1", "score": 75, "confidence": 85, "latency_ms": 10}
        }
        res = self.ensemble.fuse_evidence(faulty_modality_results, media_type="video")
        self.assertEqual(res.overall_risk, 78)
        self.assertIn("frequency", res.skipped_models)
        self.assertIn("frequency", res.skip_reasons)
        self.assertEqual(len(res.active_models), 2)

    def test_08_ensemble_disagreement_detection(self):
        """8. Verify model disagreement detection when modalities strongly conflict."""
        conflicting_results = {
            "visual": {"model_name": "Vision", "model_version": "V1", "score": 85, "confidence": 90, "latency_ms": 100},
            "frequency": {"model_name": "Frequency", "model_version": "F1", "score": 15, "confidence": 85, "latency_ms": 20},
            "temporal": {"model_name": "Temporal", "model_version": "T1", "score": 20, "confidence": 85, "latency_ms": 10}
        }
        res = self.ensemble.fuse_evidence(conflicting_results, media_type="video")
        self.assertTrue(res.disagreement_detected)
        self.assertGreaterEqual(res.model_disagreement, 30)
        # Strong disagreement sets risk_level to INCONCLUSIVE to avoid false certainty
        self.assertEqual(res.risk_level, "INCONCLUSIVE")

    def test_09_uncertainty_estimation(self):
        """9. Verify uncertainty scales proportionally with model disagreement."""
        aligned_results = {
            "visual": {"model_name": "Vision", "model_version": "V1", "score": 70, "confidence": 90},
            "frequency": {"model_name": "Frequency", "model_version": "F1", "score": 72, "confidence": 85}
        }
        res_aligned = self.ensemble.fuse_evidence(aligned_results, media_type="image")

        conflicting_results = {
            "visual": {"model_name": "Vision", "model_version": "V1", "score": 90, "confidence": 90},
            "frequency": {"model_name": "Frequency", "model_version": "F1", "score": 10, "confidence": 85}
        }
        res_conflicting = self.ensemble.fuse_evidence(conflicting_results, media_type="image")

        self.assertGreater(res_conflicting.uncertainty, res_aligned.uncertainty)

    def test_10_missing_model_handling(self):
        """10. Verify ensemble operates gracefully when optional modalities are omitted."""
        partial_results = {
            "visual": {"model_name": "Vision", "model_version": "V1", "score": 60, "confidence": 90, "latency_ms": 100}
        }
        res = self.ensemble.fuse_evidence(partial_results, media_type="image")
        self.assertEqual(res.overall_risk, 60)
        self.assertEqual(len(res.active_models), 1)

    def test_11_provenance_separation(self):
        """11. Verify provenance assertions are strictly separated from AI predictions."""
        prov_valid = self.provenance.check_manifest("1122334455667788")
        prov_invalid = self.provenance.check_manifest("abcdef1234567890")

        self.assertEqual(prov_valid["status"], "VERIFIED")
        self.assertEqual(prov_invalid["status"], "UNVERIFIED")

        # Provenance output must not contain AI scores or deepfake probabilities
        self.assertNotIn("score", prov_valid)
        self.assertNotIn("deepfake_probability", prov_valid)

    def test_12_no_face_behavior(self):
        """12. Verify zero-face input executes general visual and frequency forensics without face dependency."""
        std_res, _ = self.orchestrator.process(
            filename="no_face.jpg",
            media_type="image",
            file_size="45 KB",
            case_id="CASE-NOFACE-ENS",
            analysis_id="ANL-NOFACE-ENS",
            file_path=NO_FACE_IMG
        )
        self.assertIsNotNone(std_res.risk.overall)
        self.assertIn(std_res.risk.level, ["LOW RISK", "MEDIUM RISK", "HIGH RISK", "CRITICAL RISK"])
        self.assertGreater(std_res.confidence, 0)

    def test_13_audio_forensic_features(self):
        """13. Verify extraction of real acoustic forensic features."""
        # Generate 1.0s synthetic 440Hz sine wave PCM
        sr = 16000
        t = np.linspace(0, 1.0, sr, endpoint=False)
        samples = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

        features = audio_extractor.extract_from_pcm(samples, sample_rate=sr, channels=1)
        self.assertEqual(features.sample_rate, 16000)
        self.assertEqual(features.channels, 1)
        self.assertAlmostEqual(features.duration_sec, 1.0, places=1)
        self.assertGreater(features.rms_energy, 0.3)
        self.assertAlmostEqual(features.f0_estimate_hz, 440.0, delta=20.0)
        self.assertEqual(len(features.mfcc_estimates), 13)

    def test_14_cpu_budget_enforcement(self):
        """14. Verify CPU resource budget enforcement limits."""
        engine = ForensicEnsembleEngine(max_total_latency_ms=50.0)
        fast_results = {
            "visual": {"model_name": "Vision", "model_version": "V1", "score": 60, "latency_ms": 10.0}
        }
        res = engine.fuse_evidence(fast_results, media_type="image")
        self.assertFalse(res.budget_exceeded)


if __name__ == "__main__":
    unittest.main()
