"""
VERITAS AI — Automated Verification Suite for Phase 6B-2B
Real Deepfake Image Classifier & Multi-Face Aggregation Tests
Compatible with both pytest and python -m unittest
"""

import os
import sys
import unittest
import time
from pathlib import Path
import numpy as np
import cv2

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.models.face_detector import DetectedFace, RealFaceDetector
from app.models.image_detector import (
    ImageDetector,
    RealDeepfakeImageDetector,
    MockImageDetector,
    DeepfakeClassifierBackend,
    get_image_detector
)
from app.services.orchestrator import ForensicOrchestrator

DATA_DIR = Path(__file__).resolve().parent / "data"


class TestDeepfakeImageClassifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = DeepfakeClassifierBackend()
        cls.face_detector = RealFaceDetector()
        cls.detector = RealDeepfakeImageDetector(
            classifier_backend=cls.backend,
            face_detector=cls.face_detector
        )

    def test_01_model_loading_and_weights(self):
        """Test 6: Verify model weights exist and ONNX session loads with CPUExecutionProvider."""
        self.assertIsNotNone(self.backend)
        self.assertTrue(self.backend.model_path.exists())
        self.assertGreater(self.backend.model_path.stat().st_size, 50 * 1024 * 1024)
        self.assertIn("CPUExecutionProvider", self.backend.session.get_providers())
        self.assertEqual(self.backend.input_name, "pixel_values")
        self.assertEqual(self.backend.output_name, "logits")

    def test_02_cpu_only_inference(self):
        """Test 7: Verify inference executes on CPU without requiring CUDA."""
        dummy_crop = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        # Warm-up pass to eliminate initial ONNX initialization overhead
        _ = self.backend.predict(dummy_crop)

        t0 = time.perf_counter()
        pred = self.backend.predict(dummy_crop)
        t_ms = (time.perf_counter() - t0) * 1000

        self.assertIn("manipulation_prob", pred)
        self.assertIn("realism_prob", pred)
        self.assertIn("confidence", pred)
        self.assertIn("logits", pred)
        self.assertLess(t_ms, 800.0, "CPU inference latency should be sub-800ms on Intel CPU")

    def test_03_output_range_validation(self):
        """Test 8: Validate probabilities are within [0.0, 1.0] and sum to 1.0."""
        dummy_crop = np.zeros((224, 224, 3), dtype=np.uint8)
        pred = self.backend.predict(dummy_crop)

        self.assertGreaterEqual(pred["manipulation_prob"], 0.0)
        self.assertLessEqual(pred["manipulation_prob"], 1.0)
        self.assertGreaterEqual(pred["realism_prob"], 0.0)
        self.assertLessEqual(pred["realism_prob"], 1.0)
        self.assertAlmostEqual(pred["manipulation_prob"] + pred["realism_prob"], 1.0, places=4)
        self.assertGreaterEqual(pred["confidence"], 0.50)

    def test_04_deterministic_repeated_inference(self):
        """Test 5: Verify identical inputs produce identical outputs (zero variance)."""
        test_img = np.ones((224, 224, 3), dtype=np.uint8) * 128
        pred1 = self.backend.predict(test_img)
        pred2 = self.backend.predict(test_img)

        self.assertEqual(pred1["manipulation_prob"], pred2["manipulation_prob"])
        self.assertEqual(pred1["realism_prob"], pred2["realism_prob"])
        self.assertEqual(pred1["confidence"], pred2["confidence"])
        self.assertEqual(pred1["logits"], pred2["logits"])

    def test_05_single_face_real_inference(self):
        """Test 1: Real face crop -> Real classifier inference on single_face.jpg."""
        img_path = DATA_DIR / "single_face.jpg"
        self.assertTrue(img_path.exists())

        res = self.detector.analyze(img_path)

        self.assertEqual(res["detection_mode"], "REAL_AI")
        self.assertFalse(res["is_mock"])
        self.assertEqual(res["faces_analyzed"], 1)
        self.assertEqual(len(res["per_face_scores"]), 1)

        face_score = res["per_face_scores"][0]
        self.assertEqual(face_score["face_index"], 0)
        self.assertIn("manipulation_probability", face_score)
        self.assertIn("realism_probability", face_score)
        self.assertIn("confidence", face_score)
        self.assertIn("face_detector_confidence", face_score)
        self.assertNotEqual(face_score["manipulation_probability"], 0.91, "Must not use mock static 0.91")

        # Verify image-level score is integer 0-100
        self.assertIsInstance(res["score"], int)
        self.assertGreaterEqual(res["score"], 0)
        self.assertLessEqual(res["score"], 100)
        self.assertGreater(res["latency_ms"], 0.0)

    def test_06_multiple_face_aggregation(self):
        """Test 2 & 9: Multiple face image produces distinct per-face scores and max-pooling aggregation."""
        img_path = DATA_DIR / "multi_face.jpg"
        self.assertTrue(img_path.exists())

        res = self.detector.analyze(img_path)

        self.assertEqual(res["detection_mode"], "REAL_AI")
        self.assertGreaterEqual(res["faces_analyzed"], 2)
        self.assertEqual(len(res["per_face_scores"]), res["faces_analyzed"])

        # Check per-face scores are populated
        face_manip_probs = [f["manipulation_probability"] for f in res["per_face_scores"]]
        self.assertEqual(res["aggregation_method"], "max_pooling_with_mean_audit")
        expected_score = int(round(max(face_manip_probs) * 100))
        self.assertEqual(res["score"], expected_score)
        self.assertAlmostEqual(res["manipulation_probability"], max(face_manip_probs), places=4)

    def test_07_no_face_image_handling(self):
        """Test 3: No-face image routes to GlobalVisualForensics without face ViT execution."""
        img_path = DATA_DIR / "no_face.jpg"
        self.assertTrue(img_path.exists())

        res = self.detector.analyze(img_path)

        self.assertEqual(res["classification_status"], "ANALYZED_GENERAL_IMAGE")
        self.assertEqual(res["faces_analyzed"], 0)
        self.assertEqual(res["per_face_scores"], [])
        self.assertEqual(res["evidence_source"], "VISUAL_GLOBAL")
        self.assertEqual(res["detection_mode"], "REAL_GLOBAL_VISUAL_FORENSICS")
        self.assertIn(res["risk_level"], ["LOW RISK", "MEDIUM RISK", "HIGH RISK", "CRITICAL RISK"])
        self.assertIsInstance(res["score"], int)

    def test_08_invalid_image_handling(self):
        """Test 4: Invalid input (None, non-existent path, empty array) returns safe error payload."""
        res_none = self.detector.analyze(None)
        self.assertEqual(res_none["score"], 0)
        self.assertEqual(res_none["faces_analyzed"], 0)
        self.assertIn("error", res_none)

        res_missing = self.detector.analyze("non_existent_file_path_12345.jpg")
        self.assertEqual(res_missing["score"], 0)
        self.assertEqual(res_missing["faces_analyzed"], 0)

        res_empty = self.detector.analyze(np.zeros((0, 0, 3), dtype=np.uint8))
        self.assertEqual(res_empty["score"], 0)

    def test_09_mock_image_detector_fallback(self):
        """Test 10: Verify MockImageDetector is labeled as simulated demo mode."""
        mock_det = MockImageDetector()
        res = mock_det.analyze("test.jpg")

        self.assertTrue(res["is_mock"])
        self.assertEqual(res["detection_mode"], "DEMO MODE // SIMULATED IMAGE DETECTION")
        self.assertEqual(res["score"], 91)
        self.assertEqual(res["confidence"], 94)

    def test_10_orchestrator_end_to_end_integration(self):
        """Verify full orchestrator pipeline with RealDeepfakeImageDetector."""
        orch = ForensicOrchestrator(image_detector=self.detector)
        img_path = DATA_DIR / "single_face.jpg"

        std_res, db_payload = orch.process(
            filename="single_face.jpg",
            media_type="image",
            file_size="91.8 KB",
            case_id="CASE-VERIFY-6B",
            analysis_id="ANL-VERIFY-6B",
            file_path=img_path
        )

        self.assertEqual(std_res.media_type, "image")
        self.assertGreaterEqual(std_res.risk.overall, 0)
        self.assertLessEqual(std_res.risk.overall, 100)
        self.assertEqual(std_res.visual.score, self.detector.analyze(img_path)["score"])
        self.assertIn(std_res.risk.level, ["LOW RISK", "MEDIUM RISK", "HIGH RISK", "CRITICAL RISK"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
