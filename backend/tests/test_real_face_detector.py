"""
VERITAS AI — Automated Verification Suite for Phase 6B-2A
Real Face Detection Adapter & Video Frame Sampling Tests
Compatible with both pytest and python -m unittest
"""

import os
import sys
import unittest
from pathlib import Path
import numpy as np
import cv2

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.models.face_detector import (
    FaceDetector,
    RealFaceDetector,
    MockFaceDetector,
    DetectedFace,
    SimpleFaceTracker,
    get_face_detector
)
from app.services.media_processor import media_processor, MediaProcessor


DATA_DIR = Path(__file__).resolve().parent / "data"


class TestRealFaceDetector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real_detector = RealFaceDetector()

    def test_01_real_detector_initialization(self):
        """Verify RealFaceDetector loads OpenCV YuNet and weights correctly."""
        self.assertIsNotNone(self.real_detector)
        self.assertTrue(self.real_detector.model_path.exists())
        self.assertIsNotNone(self.real_detector.detector)

    def test_02_single_face_detection(self):
        """Verify single face image produces 1 face with real bounding box and confidence."""
        img_path = DATA_DIR / "single_face.jpg"
        self.assertTrue(img_path.exists(), "Test asset single_face.jpg missing")

        bgr = cv2.imread(str(img_path))
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        faces = self.real_detector.detect_faces(rgb, frame_number=1, timestamp_sec=0.0)

        self.assertEqual(len(faces), 1)
        face = faces[0]

        # Verify real confidence is a continuous float > 0.8
        self.assertGreaterEqual(face.confidence, 0.80)
        self.assertLessEqual(face.confidence, 1.0)
        self.assertNotEqual(face.confidence, 0.96, "Must not use hardcoded heuristic 0.96")

        # Verify bounding box coordinates
        self.assertGreater(face.x, 0)
        self.assertGreater(face.y, 0)
        self.assertGreater(face.width, 50)
        self.assertGreater(face.height, 50)
        self.assertEqual(face.bbox, (face.x, face.y, face.width, face.height))

        # Verify 5-point landmarks
        self.assertTrue(face.landmarks_ready)
        self.assertEqual(len(face.landmarks), 5)
        for lx, ly in face.landmarks:
            self.assertGreater(lx, 0)
            self.assertGreater(ly, 0)

        # Verify normalized crop shape (224, 224, 3) and tensor shape (3, 224, 224)
        self.assertIsNotNone(face.face_crop)
        self.assertEqual(face.face_crop.shape, (224, 224, 3))
        self.assertEqual(face.crop_tensor_shape, (3, 224, 224))

        # Verify metadata flags
        self.assertFalse(face.is_mock)
        self.assertEqual(face.detection_mode, "REAL_AI_YUNET")

    def test_03_multiple_faces_detection(self):
        """Verify multiple faces are detected with distinct coordinates and confidences."""
        img_path = DATA_DIR / "multi_face.jpg"
        self.assertTrue(img_path.exists(), "Test asset multi_face.jpg missing")

        bgr = cv2.imread(str(img_path))
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        faces = self.real_detector.detect_faces(rgb, frame_number=1, timestamp_sec=0.0)

        self.assertGreaterEqual(len(faces), 2)
        # Verify confidences differ and are not hardcoded
        confidences = [f.confidence for f in faces]
        self.assertEqual(len(set(confidences)), len(confidences), "Detected faces must have distinct real confidence scores")
        for f in faces:
            self.assertGreaterEqual(f.confidence, 0.0)
            self.assertLessEqual(f.confidence, 1.0)
            self.assertGreater(f.width, 0)
            self.assertGreater(f.height, 0)
            self.assertEqual(f.face_crop.shape, (224, 224, 3))

    def test_04_no_face_detection(self):
        """Verify images with no faces return empty list without error."""
        img_path = DATA_DIR / "no_face.jpg"
        self.assertTrue(img_path.exists(), "Test asset no_face.jpg missing")

        bgr = cv2.imread(str(img_path))
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        faces = self.real_detector.detect_faces(rgb, frame_number=1, timestamp_sec=0.0)

        self.assertIsInstance(faces, list)
        self.assertEqual(len(faces), 0)

    def test_05_invalid_and_empty_images(self):
        """Verify invalid inputs return empty lists gracefully."""
        self.assertEqual(self.real_detector.detect_faces(None), [])
        self.assertEqual(self.real_detector.detect_faces(np.zeros((0, 0, 3), dtype=np.uint8)), [])
        self.assertEqual(self.real_detector.detect_faces(np.zeros((4, 4, 3), dtype=np.uint8)), [])

    def test_06_mock_face_detector_fallback(self):
        """Verify MockFaceDetector is clearly labeled as simulated demo mode."""
        mock_det = MockFaceDetector()
        dummy_img = np.zeros((300, 300, 3), dtype=np.uint8)
        faces = mock_det.detect_faces(dummy_img, frame_number=2, timestamp_sec=1.5)

        self.assertEqual(len(faces), 1)
        face = faces[0]
        self.assertTrue(face.is_mock)
        self.assertEqual(face.detection_mode, "DEMO MODE // SIMULATED FACE DETECTION")
        self.assertEqual(face.frame_number, 2)
        self.assertEqual(face.timestamp_sec, 1.5)

    def test_07_simple_face_tracker(self):
        """Verify multi-frame face tracking preserves IDs across frames."""
        tracker = SimpleFaceTracker(max_distance_pixels=50.0)

        # Frame 1: Face at (100, 100)
        face_f1 = DetectedFace(x=100, y=100, width=50, height=50, confidence=0.92, frame_number=1)
        tracked_f1 = tracker.track([face_f1])
        track_id_1 = tracked_f1[0].tracking_id
        self.assertIsNotNone(track_id_1)

        # Frame 2: Face moved slightly to (105, 102)
        face_f2 = DetectedFace(x=105, y=102, width=50, height=50, confidence=0.93, frame_number=2)
        tracked_f2 = tracker.track([face_f2])
        self.assertEqual(tracked_f2[0].tracking_id, track_id_1, "Expected tracker to maintain track ID for nearby face")

    def test_08_video_sampled_frames_detection(self):
        """Verify video preprocessing runs face detection on sampled frames."""
        vid_path = DATA_DIR / "sample_face_video.mp4"
        self.assertTrue(vid_path.exists(), "Test video sample_face_video.mp4 missing")

        meta, sampled_frames, temporal_meta = media_processor.preprocess_video(vid_path, "sample_face_video.mp4")

        self.assertEqual(meta.media_type, "video")
        self.assertGreaterEqual(len(sampled_frames), 2)
        self.assertEqual(temporal_meta["sampled_frame_count"], len(sampled_frames))

        for sf in sampled_frames:
            self.assertEqual(sf.width, 640)
            self.assertEqual(sf.height, 480)
            self.assertGreaterEqual(sf.timestamp_sec, 0.0)
            if sf.faces:
                self.assertFalse(sf.faces[0].is_mock)
                self.assertIsNotNone(sf.faces[0].tracking_id)

    def test_09_media_processor_image_ingestion_integration(self):
        """Verify full media processor pipeline with RealFaceDetector."""
        img_path = DATA_DIR / "single_face.jpg"
        res = media_processor.process_media_file(img_path, "single_face.jpg")

        self.assertEqual(res["media_type"], "image")
        self.assertIn("metadata", res)
        self.assertIn("faces", res)
        self.assertEqual(len(res["faces"]), 1)
        face_dict = res["faces"][0]
        self.assertFalse(face_dict["is_mock"])
        self.assertGreater(face_dict["confidence"], 0.8)
        self.assertIn("crop_shape", face_dict)


if __name__ == "__main__":
    unittest.main(verbosity=2)
