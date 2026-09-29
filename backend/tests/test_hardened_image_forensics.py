"""
VERITAS AI — Automated Verification Suite for Phase 6B-2C
Hardened Real Image Forensics & Safe No-Face Semantics Tests
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
    get_image_detector,
    MODEL_LIMITATIONS
)
from app.services.orchestrator import ForensicOrchestrator

DATA_DIR = Path(__file__).resolve().parent / "data"


class TestHardenedImageForensics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = DeepfakeClassifierBackend()
        cls.face_detector = RealFaceDetector()
        cls.detector = RealDeepfakeImageDetector(
            classifier_backend=cls.backend,
            face_detector=cls.face_detector
        )

    def test_01_single_face_real_classifier(self):
        """Test 1: Single face image triggers face detection and real ViT classifier."""
        img_path = DATA_DIR / "single_face.jpg"
        self.assertTrue(img_path.exists())

        res = self.detector.analyze(img_path)

        self.assertEqual(res["classification_status"], "ANALYZED")
        self.assertEqual(res["detection_mode"], "REAL_AI")
        self.assertFalse(res["is_mock"])
        self.assertEqual(res["faces_detected"], 1)
        self.assertEqual(res["faces_analyzed"], 1)
        self.assertIsNotNone(res["image_manipulation_score"])
        self.assertIsNotNone(res["prediction_confidence"])

        face = res["faces"][0]
        self.assertEqual(face["face_id"], 0)
        self.assertGreater(face["manipulation_probability"], 0.0)
        self.assertLess(face["manipulation_probability"], 1.0)
        self.assertGreaterEqual(face["prediction_confidence"], 0.50)

    def test_02_multiple_faces_real_classifier(self):
        """Test 2: Multiple face image analyzes each face individually."""
        img_path = DATA_DIR / "multi_face.jpg"
        self.assertTrue(img_path.exists())

        res = self.detector.analyze(img_path)

        self.assertEqual(res["classification_status"], "ANALYZED")
        self.assertGreaterEqual(res["faces_detected"], 2)
        self.assertEqual(len(res["faces"]), res["faces_detected"])

    def test_03_no_face_does_not_call_classifier(self):
        """Test 3: Zero-face image MUST NOT invoke the ViT deepfake classifier."""
        img_path = DATA_DIR / "no_face.jpg"
        self.assertTrue(img_path.exists())

        initial_calls = self.backend.call_count
        res = self.detector.analyze(img_path)
        calls_after = self.backend.call_count

        self.assertEqual(
            initial_calls,
            calls_after,
            f"Classifier predict() should NOT be called for zero-face image! Expected {initial_calls}, got {calls_after}."
        )

    def test_04_no_face_general_image_forensics(self):
        """Test 4: Zero-face image performs content-agnostic general visual forensics without ViT."""
        img_path = DATA_DIR / "no_face.jpg"
        self.assertTrue(img_path.exists())

        res = self.detector.analyze(img_path)

        self.assertEqual(res["classification_status"], "ANALYZED_GENERAL_IMAGE")
        self.assertEqual(res["evidence_source"], "VISUAL_GLOBAL")
        self.assertEqual(res["faces_detected"], 0)
        self.assertEqual(res["faces_analyzed"], 0)
        self.assertIsNotNone(res["score"])
        self.assertIsNotNone(res["prediction_confidence"])
        self.assertIn(res["risk_level"], ("LOW RISK", "MEDIUM RISK", "HIGH RISK", "CRITICAL RISK"))
        self.assertEqual(res["faces"], [])
        self.assertIn("Content-agnostic visual forensics", res["explanation"])

    def test_05_invalid_image_structured_error(self):
        """Test 5: Corrupted or invalid inputs return ANALYSIS_ERROR structured response."""
        res_none = self.detector.analyze(None)
        self.assertEqual(res_none["classification_status"], "ANALYSIS_ERROR")
        self.assertEqual(res_none["faces_detected"], 0)
        self.assertIsNone(res_none["image_manipulation_score"])

        res_empty = self.detector.analyze(np.zeros((0, 0, 3), dtype=np.uint8))
        self.assertEqual(res_empty["classification_status"], "ANALYSIS_ERROR")

        res_missing = self.detector.analyze("non_existent_file_path_xyz.jpg")
        self.assertEqual(res_missing["classification_status"], "ANALYSIS_ERROR")

    def test_06_per_face_evidence_preserved(self):
        """Test 6: Every detected face preserves individual bounding box, landmarks, probabilities."""
        img_path = DATA_DIR / "multi_face.jpg"
        res = self.detector.analyze(img_path)

        for idx, face in enumerate(res["faces"]):
            self.assertEqual(face["face_id"], idx)
            self.assertIn("bounding_box", face)
            self.assertEqual(len(face["bounding_box"]), 4)
            self.assertIn("manipulation_probability", face)
            self.assertIn("realism_probability", face)
            self.assertIn("prediction_confidence", face)
            self.assertIn("inference_latency_ms", face)
            self.assertIn("model_name", face)
            self.assertIn("model_version", face)

    def test_07_max_aggregation(self):
        """Test 7: Image manipulation score equals maximum observed face manipulation probability."""
        img_path = DATA_DIR / "multi_face.jpg"
        res = self.detector.analyze(img_path)

        face_scores = [f["manipulation_probability"] for f in res["faces"]]
        self.assertAlmostEqual(res["image_manipulation_score"], max(face_scores), places=4)
        self.assertEqual(res["aggregation_method"], "max_pooling_with_mean_audit")

    def test_08_mean_aggregation(self):
        """Test 8: Mean face score equals average of all detected face manipulation probabilities."""
        img_path = DATA_DIR / "multi_face.jpg"
        res = self.detector.analyze(img_path)

        face_scores = [f["manipulation_probability"] for f in res["faces"]]
        expected_mean = sum(face_scores) / len(face_scores)
        self.assertAlmostEqual(res["mean_face_score"], expected_mean, places=4)

    def test_09_highest_risk_face_tracking(self):
        """Test 9: Highest risk face ID points to the face with the maximum manipulation probability."""
        img_path = DATA_DIR / "multi_face.jpg"
        res = self.detector.analyze(img_path)

        highest_id = res["highest_risk_face_id"]
        highest_face = res["faces"][highest_id]
        self.assertEqual(highest_face["manipulation_probability"], res["image_manipulation_score"])

    def test_10_prediction_confidence_semantics(self):
        """Test 10: prediction_confidence is max(P(Realism), P(Deepfake))."""
        dummy_crop = np.ones((224, 224, 3), dtype=np.uint8) * 100
        pred = self.backend.predict(dummy_crop)

        expected_conf = max(pred["realism_prob"], pred["manipulation_prob"])
        self.assertAlmostEqual(pred["prediction_confidence"], expected_conf, places=5)
        self.assertGreaterEqual(pred["prediction_confidence"], 0.50)

    def test_11_model_metadata_and_limitations(self):
        """Test 11: Model metadata and limitations are explicitly exposed."""
        metadata = self.detector.model_metadata
        self.assertEqual(metadata["model_name"], "VERITAS-VISION")
        self.assertEqual(metadata["model_version"], "v1.0-ONNX-INT8")
        self.assertEqual(metadata["model_license"], "Apache-2.0")
        self.assertEqual(metadata["execution_provider"], "CPUExecutionProvider")
        self.assertEqual(metadata["quantization"], "INT8")
        self.assertFalse(metadata["is_mock"])

        res = self.detector.analyze(DATA_DIR / "single_face.jpg")
        self.assertIn("limitations", res)
        self.assertEqual(res["limitations"], MODEL_LIMITATIONS)

    def test_12_deterministic_inference(self):
        """Test 12: Repeated inference on same crop produces identical results."""
        dummy_crop = np.random.RandomState(42).randint(0, 255, (224, 224, 3), dtype=np.uint8)
        pred1 = self.backend.predict(dummy_crop)
        pred2 = self.backend.predict(dummy_crop)

        self.assertEqual(pred1["manipulation_prob"], pred2["manipulation_prob"])
        self.assertEqual(pred1["prediction_confidence"], pred2["prediction_confidence"])
        self.assertEqual(pred1["logits"], pred2["logits"])

    def test_13_mock_fallback_mode(self):
        """Test 13: MockImageDetector explicitly reports DEMO_MODE and is_mock=True."""
        mock_det = MockImageDetector()
        res = mock_det.analyze("dummy.jpg")

        self.assertEqual(res["classification_status"], "DEMO_MODE")
        self.assertTrue(res["is_mock"])
        self.assertEqual(res["detection_mode"], "DEMO MODE // SIMULATED IMAGE DETECTION")

    def test_14_orchestrator_general_image_integration(self):
        """Test 14: Orchestrator integration handles no-face image with general visual & frequency forensics."""
        orch = ForensicOrchestrator(image_detector=self.detector)
        no_face_path = DATA_DIR / "no_face.jpg"

        std_res, db_payload = orch.process(
            filename="no_face.jpg",
            media_type="image",
            file_size="44.7 KB",
            case_id="CASE-NOFACE-1",
            analysis_id="ANL-NOFACE-1",
            file_path=no_face_path
        )

        self.assertEqual(std_res.media_type, "image")
        self.assertIsNotNone(std_res.risk.overall)
        self.assertIn(std_res.risk.level, ("LOW RISK", "MEDIUM RISK", "HIGH RISK", "CRITICAL RISK"))
        self.assertGreater(std_res.confidence, 0)
        self.assertEqual(std_res.status, "COMPLETE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
