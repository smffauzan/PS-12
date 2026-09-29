"""
VERITAS AI — Video Frame-Level Forensics & Temporal Analysis Test Suite
Module: backend.tests.test_video_forensics

Tests the real OpenCV YuNet + ViT video forensic pipeline, multi-frame tracking,
temporal stability metrics, zero-face handling, timeline events, orchestrator integration,
and mock fallback safety.
"""

import unittest
from pathlib import Path
import numpy as np
import cv2

from app.services.video_forensics import (
    video_forensic_engine,
    RealVideoForensicEngine,
    TemporalForensicAnalyzer,
    VideoSamplingConfig,
    TrackedFaceObservation
)
from app.models.video_detector import RealVideoDetector, MockVideoDetector, get_video_detector
from app.models.temporal_detector import RealTemporalDetector, MockTemporalDetector, get_temporal_detector
from app.models.face_detector import get_face_detector, SimpleFaceTracker
from app.services.orchestrator import ForensicOrchestrator

DATA_DIR = Path(__file__).resolve().parent / "data"
SAMPLE_FACE_VIDEO = DATA_DIR / "sample_face_video.mp4"
MULTI_FACE_VIDEO = DATA_DIR / "multi_face_video.mp4"
NO_FACE_VIDEO = DATA_DIR / "no_face_video.mp4"


class TestVideoForensics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = video_forensic_engine
        cls.video_detector = RealVideoDetector()
        cls.temporal_detector = RealTemporalDetector()
        cls.orchestrator = ForensicOrchestrator(
            video_detector=cls.video_detector,
            temporal_detector=cls.temporal_detector
        )

    def test_video_frame_sampling(self):
        """1. Verify configurable frame sampling without buffering entire video."""
        config_1fps = VideoSamplingConfig(sample_interval_sec=1.0, max_sample_frames=10)
        res_1fps = self.engine.analyze_video(SAMPLE_FACE_VIDEO, sampling_config=config_1fps)
        
        self.assertEqual(res_1fps["classification_status"], "ANALYZED")
        self.assertGreaterEqual(res_1fps["sampled_frames_count"], 2)
        self.assertLessEqual(res_1fps["sampled_frames_count"], 10)
        self.assertGreater(res_1fps["video_duration_sec"], 0)
        self.assertGreater(res_1fps["video_fps"], 0)

    def test_video_timestamp_preservation(self):
        """2. Verify exact preservation of frame index and timestamp seconds."""
        res = self.engine.analyze_video(SAMPLE_FACE_VIDEO)
        self.assertEqual(res["classification_status"], "ANALYZED")
        self.assertGreater(len(res["tracks"]), 0)

        track = res["tracks"][0]
        self.assertIn("observations", track)
        for obs in track["observations"]:
            self.assertIn("frame_index", obs)
            self.assertIn("timestamp_sec", obs)
            self.assertGreaterEqual(obs["frame_index"], 0)
            self.assertGreaterEqual(obs["timestamp_sec"], 0.0)

    def test_video_face_detection(self):
        """3. Verify real YuNet face detector discovers faces on video frames."""
        res = self.engine.analyze_video(SAMPLE_FACE_VIDEO)
        self.assertEqual(res["classification_status"], "ANALYZED")
        self.assertGreater(res["frames_with_faces"], 0)
        self.assertGreater(res["total_faces_detected"], 0)
        self.assertFalse(res["is_mock"])
        self.assertEqual(res["detection_mode"], "REAL_AI_VIDEO")

    def test_video_tracking(self):
        """4. Verify multi-frame face tracking across sampled frames."""
        res = self.engine.analyze_video(SAMPLE_FACE_VIDEO)
        self.assertIn("tracking_ids", res)
        self.assertGreater(len(res["tracking_ids"]), 0)
        
        # Verify tracks retain consistent tracking_id
        for track in res["tracks"]:
            trk_id = track["tracking_id"]
            for obs in track["observations"]:
                self.assertEqual(obs["tracking_id"], trk_id)

    def test_real_vit_frame_inference(self):
        """5. Verify real ViT classifier performs inference on detected face crops."""
        res = self.engine.analyze_video(SAMPLE_FACE_VIDEO)
        track = res["tracks"][0]
        for obs in track["observations"]:
            self.assertIn("manipulation_probability", obs)
            self.assertIn("realism_probability", obs)
            self.assertIn("prediction_confidence", obs)
            self.assertIn("inference_latency_ms", obs)
            self.assertGreaterEqual(obs["manipulation_probability"], 0.0)
            self.assertLessEqual(obs["manipulation_probability"], 1.0)
            self.assertAlmostEqual(
                obs["manipulation_probability"] + obs["realism_probability"],
                1.0,
                places=3
            )
            self.assertGreater(obs["inference_latency_ms"], 0.0)

    def test_per_track_aggregation(self):
        """6. Verify per-track statistical aggregation (mean, max, min, std, range)."""
        res = self.engine.analyze_video(SAMPLE_FACE_VIDEO)
        for track in res["tracks"]:
            obs_probs = [o["manipulation_probability"] for o in track["observations"]]
            expected_mean = float(np.mean(obs_probs))
            expected_max = float(np.max(obs_probs))
            expected_min = float(np.min(obs_probs))
            expected_range = expected_max - expected_min

            self.assertAlmostEqual(track["mean_manipulation_probability"], expected_mean, places=3)
            self.assertAlmostEqual(track["max_manipulation_probability"], expected_max, places=3)
            self.assertAlmostEqual(track["min_manipulation_probability"], expected_min, places=3)
            self.assertAlmostEqual(track["score_range"], expected_range, places=3)

    def test_temporal_feature_calculation(self):
        """7. Verify mathematical calculation of temporal stability features."""
        res = self.engine.analyze_video(SAMPLE_FACE_VIDEO)
        for track in res["tracks"]:
            self.assertIn("detection_coverage", track)
            self.assertIn("detection_continuity", track)
            self.assertIn("bbox_instability", track)
            self.assertIn("landmark_instability", track)
            self.assertIn("temporal_gaps", track)
            self.assertGreaterEqual(track["detection_coverage"], 0.0)
            self.assertLessEqual(track["detection_coverage"], 1.0)
            self.assertGreaterEqual(track["detection_continuity"], 0.0)
            self.assertLessEqual(track["detection_continuity"], 1.0)
            self.assertGreaterEqual(track["bbox_instability"], 0.0)
            self.assertGreaterEqual(track["landmark_instability"], 0.0)

    def test_temporal_anomaly_score(self):
        """8. Verify documented temporal anomaly formula calculation."""
        analyzer = TemporalForensicAnalyzer()
        obs = [
            TrackedFaceObservation(
                frame_index=0, timestamp_sec=0.0, face_id=0, tracking_id=1,
                bbox=(100, 100, 80, 80), landmarks=[(120, 120), (160, 120), (140, 140), (130, 160), (150, 160)],
                face_detector_confidence=0.95, manipulation_probability=0.20,
                realism_probability=0.80, prediction_confidence=0.80, inference_latency_ms=10.0
            ),
            TrackedFaceObservation(
                frame_index=30, timestamp_sec=1.0, face_id=0, tracking_id=1,
                bbox=(102, 101, 80, 80), landmarks=[(122, 121), (162, 121), (142, 141), (132, 161), (152, 161)],
                face_detector_confidence=0.96, manipulation_probability=0.80,
                realism_probability=0.20, prediction_confidence=0.80, inference_latency_ms=10.0
            )
        ]
        summary = analyzer.analyze_track(
            tracking_id=1, observations=obs, total_sampled_frames=2,
            sample_interval_sec=1.0, frame_width=640, frame_height=480
        )
        self.assertGreaterEqual(summary.temporal_anomaly_score, 0)
        self.assertLessEqual(summary.temporal_anomaly_score, 100)
        self.assertGreater(summary.score_std, 0.20)

    def test_timeline_generation(self):
        """9. Verify timeline events are grounded in actual sampled frame timestamps."""
        res = self.engine.analyze_video(SAMPLE_FACE_VIDEO)
        self.assertIn("timeline", res)
        self.assertIsInstance(res["timeline"], list)
        if len(res["timeline"]) > 0:
            for ev in res["timeline"]:
                self.assertIn("timestampSec", ev)
                self.assertIn("formattedTime", ev)
                self.assertIn("frameNumber", ev)
                self.assertIn("visualScore", ev)
                self.assertIn("explanation", ev)
                self.assertGreaterEqual(ev["timestampSec"], 0.0)

    def test_no_face_video(self):
        """10. Verify zero-face video bypasses ViT and returns ANALYZED_GENERAL_VIDEO with general forensics."""
        res = self.engine.analyze_video(NO_FACE_VIDEO)
        self.assertEqual(res["classification_status"], "ANALYZED_GENERAL_VIDEO")
        self.assertIn(res["risk_level"], ("LOW RISK", "MEDIUM RISK", "HIGH RISK", "CRITICAL RISK"))
        self.assertIsNotNone(res["score"])
        self.assertGreaterEqual(res["confidence"], 80)
        self.assertIsNotNone(res["frame_level_max_risk"])
        self.assertIsNotNone(res["frame_level_mean_risk"])
        self.assertIsNotNone(res["temporal_anomaly_score"])
        self.assertEqual(res["total_faces_detected"], 0)
        self.assertEqual(res["performance"]["vit_total_ms"], 0.0)

        # Test via TemporalDetector model wrapper
        temp_res = self.temporal_detector.analyze(NO_FACE_VIDEO)
        self.assertEqual(temp_res["classification_status"], "ANALYZED_GENERAL_VIDEO")
        self.assertIsNotNone(temp_res["score"])
        self.assertGreater(temp_res["confidence"], 0)

    def test_invalid_video(self):
        """11. Verify graceful error handling on nonexistent/invalid video files."""
        fake_path = DATA_DIR / "non_existent_file_999.mp4"
        res = self.engine.analyze_video(fake_path)
        self.assertEqual(res["classification_status"], "ANALYSIS_ERROR")
        self.assertEqual(res["risk_level"], "INCONCLUSIVE")
        self.assertEqual(res["score"], 0)

    def test_deterministic_video_analysis(self):
        """12. Verify video forensic analysis is strictly deterministic across multiple runs."""
        res1 = self.engine.analyze_video(SAMPLE_FACE_VIDEO)
        res2 = self.engine.analyze_video(SAMPLE_FACE_VIDEO)

        self.assertEqual(res1["classification_status"], res2["classification_status"])
        self.assertEqual(res1["sampled_frames_count"], res2["sampled_frames_count"])
        self.assertEqual(res1["total_faces_detected"], res2["total_faces_detected"])
        self.assertEqual(res1["score"], res2["score"])
        self.assertAlmostEqual(res1["frame_level_max_risk"], res2["frame_level_max_risk"], places=4)
        self.assertAlmostEqual(res1["frame_level_mean_risk"], res2["frame_level_mean_risk"], places=4)
        self.assertEqual(res1["temporal_anomaly_score"], res2["temporal_anomaly_score"])

    def test_orchestrator_video_integration(self):
        """13. Verify full orchestrator pipeline with real video ingestion."""
        std_res, db_payload = self.orchestrator.process(
            filename="sample_face_video.mp4",
            media_type="video",
            file_size="500 KB",
            case_id="CASE-TEST-VID-1",
            analysis_id="ANL-TEST-VID-1",
            file_path=SAMPLE_FACE_VIDEO
        )
        self.assertEqual(std_res.status, "COMPLETE")
        self.assertIn("REAL AI VIDEO", std_res.model_version)
        self.assertGreater(std_res.visual.score, 0)
        self.assertGreater(len(std_res.timeline), 0)
        self.assertGreater(db_payload["visual_score"], 0)

    def test_orchestrator_no_face_video(self):
        """14. Verify orchestrator on no-face video performs content-agnostic forensics without errors."""
        std_res, db_payload = self.orchestrator.process(
            filename="no_face_video.mp4",
            media_type="video",
            file_size="200 KB",
            case_id="CASE-TEST-NOFACE-VID",
            analysis_id="ANL-TEST-NOFACE-VID",
            file_path=NO_FACE_VIDEO
        )
        self.assertEqual(std_res.status, "COMPLETE")
        self.assertIsNotNone(std_res.risk.overall)
        self.assertIn(std_res.risk.level, ("LOW RISK", "MEDIUM RISK", "HIGH RISK", "CRITICAL RISK"))
        self.assertGreater(std_res.confidence, 0)
        self.assertGreater(len(std_res.timeline), 0)

    def test_mock_fallback_mode(self):
        """15. Verify MockVideoDetector & MockTemporalDetector operate safely in fallback."""
        mock_vid = MockVideoDetector()
        mock_tmp = MockTemporalDetector()
        self.assertTrue(mock_vid.is_mock)
        self.assertTrue(mock_tmp.is_mock)
        self.assertIn("DEMO MODE", mock_vid.detection_mode)
        self.assertIn("DEMO MODE", mock_tmp.detection_mode)

        res_v = mock_vid.analyze("dummy.mp4")
        res_t = mock_tmp.analyze("dummy.mp4")
        self.assertEqual(res_v["score"], 91)
        self.assertEqual(res_t["score"], 84)


if __name__ == "__main__":
    unittest.main()
