"""
VERITAS AI — Advanced Video Forensic Evidence Windows Test Suite
Module: backend.tests.test_evidence_windows

Validates score sequences, suspicious interval detection, timeline clustering,
evidence severity rules, highest-risk interval ranking, no-face semantics,
and temporary frame data cleanup.
"""

import unittest
from pathlib import Path
import numpy as np
import tempfile
import cv2

from app.services.video_forensics import (
    video_forensic_engine,
    RealVideoForensicEngine,
    TemporalForensicAnalyzer,
    EvidenceWindowDetector,
    EvidenceWindowConfig,
    VideoSamplingConfig,
    TrackedFaceObservation,
    FaceTrackSummary,
    ScoreSequencePoint
)
from app.models.video_detector import RealVideoDetector, MockVideoDetector
from app.models.temporal_detector import RealTemporalDetector, MockTemporalDetector
from app.services.orchestrator import ForensicOrchestrator
from app.services.media_processor import temporary_media_workspace

DATA_DIR = Path(__file__).resolve().parent / "data"
SAMPLE_FACE_VIDEO = DATA_DIR / "sample_face_video.mp4"
MULTI_FACE_VIDEO = DATA_DIR / "multi_face_video.mp4"
NO_FACE_VIDEO = DATA_DIR / "no_face_video.mp4"


class TestForensicEvidenceWindows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = video_forensic_engine
        cls.video_detector = RealVideoDetector()
        cls.temporal_detector = RealTemporalDetector()
        cls.orchestrator = ForensicOrchestrator(
            video_detector=cls.video_detector,
            temporal_detector=cls.temporal_detector
        )

    def test_01_score_sequence_generation(self):
        """1. Verify chronological score sequence generation for each tracking ID."""
        res = self.engine.analyze_video(SAMPLE_FACE_VIDEO)
        self.assertIn("score_sequences", res)
        self.assertIsInstance(res["score_sequences"], dict)
        self.assertGreater(len(res["score_sequences"]), 0)

        for trk_id, seq in res["score_sequences"].items():
            self.assertGreater(len(seq), 0)
            prev_t = -1.0
            for pt in seq:
                self.assertIn("frame_index", pt)
                self.assertIn("timestamp_sec", pt)
                self.assertIn("manipulation_probability", pt)
                self.assertIn("realism_probability", pt)
                self.assertIn("prediction_confidence", pt)
                self.assertGreaterEqual(pt["timestamp_sec"], prev_t)
                prev_t = pt["timestamp_sec"]

    def test_02_high_score_evidence_window(self):
        """2. Verify detection of evidence window on high manipulation probability."""
        detector = EvidenceWindowDetector(EvidenceWindowConfig(high_probability_threshold=0.60))
        obs = [
            TrackedFaceObservation(
                frame_index=0, timestamp_sec=0.0, face_id=0, tracking_id=0,
                bbox=(50, 50, 80, 80), landmarks=None, face_detector_confidence=0.95,
                manipulation_probability=0.20, realism_probability=0.80, prediction_confidence=0.80, inference_latency_ms=10.0
            ),
            TrackedFaceObservation(
                frame_index=30, timestamp_sec=1.0, face_id=0, tracking_id=0,
                bbox=(52, 50, 80, 80), landmarks=None, face_detector_confidence=0.95,
                manipulation_probability=0.75, realism_probability=0.25, prediction_confidence=0.85, inference_latency_ms=10.0
            )
        ]
        track = FaceTrackSummary(
            tracking_id=0, frames_analyzed=2, first_timestamp=0.0, last_timestamp=1.0, duration_sec=1.0,
            mean_manipulation_probability=0.475, max_manipulation_probability=0.75, min_manipulation_probability=0.20,
            score_std=0.275, score_range=0.55, detection_coverage=1.0, detection_continuity=1.0,
            bbox_instability=0.02, landmark_instability=0.0, temporal_gaps=[], temporal_anomaly_score=25,
            observations=obs
        )
        windows, highest_risk = detector.detect_windows([track])
        self.assertGreater(len(windows), 0)
        high_win = [w for w in windows if "HIGH_MANIPULATION_PROBABILITY" in w.trigger_types]
        self.assertEqual(len(high_win), 1)
        self.assertAlmostEqual(high_win[0].peak_manipulation_probability, 0.75, places=2)

    def test_03_sudden_score_change_evidence(self):
        """3. Verify detection of evidence window on sudden score variance jump."""
        detector = EvidenceWindowDetector(EvidenceWindowConfig(score_jump_threshold=0.30))
        obs = [
            TrackedFaceObservation(
                frame_index=0, timestamp_sec=0.0, face_id=0, tracking_id=0,
                bbox=(50, 50, 80, 80), landmarks=None, face_detector_confidence=0.95,
                manipulation_probability=0.15, realism_probability=0.85, prediction_confidence=0.85, inference_latency_ms=10.0
            ),
            TrackedFaceObservation(
                frame_index=30, timestamp_sec=1.0, face_id=0, tracking_id=0,
                bbox=(52, 50, 80, 80), landmarks=None, face_detector_confidence=0.95,
                manipulation_probability=0.65, realism_probability=0.35, prediction_confidence=0.85, inference_latency_ms=10.0
            )
        ]
        track = FaceTrackSummary(
            tracking_id=0, frames_analyzed=2, first_timestamp=0.0, last_timestamp=1.0, duration_sec=1.0,
            mean_manipulation_probability=0.40, max_manipulation_probability=0.65, min_manipulation_probability=0.15,
            score_std=0.25, score_range=0.50, detection_coverage=1.0, detection_continuity=1.0,
            bbox_instability=0.02, landmark_instability=0.0, temporal_gaps=[], temporal_anomaly_score=30,
            observations=obs
        )
        windows, highest_risk = detector.detect_windows([track])
        self.assertGreater(len(windows), 0)
        jump_win = [w for w in windows if "SUDDEN_SCORE_CHANGE" in w.trigger_types]
        self.assertEqual(len(jump_win), 1)
        self.assertEqual(jump_win[0].trigger_type, "SUDDEN_SCORE_CHANGE")

    def test_04_temporal_anomaly_evidence(self):
        """4. Verify evidence window triggered by high temporal anomaly score."""
        detector = EvidenceWindowDetector(EvidenceWindowConfig(temporal_anomaly_threshold=40))
        obs = [
            TrackedFaceObservation(
                frame_index=0, timestamp_sec=0.0, face_id=0, tracking_id=0,
                bbox=(50, 50, 80, 80), landmarks=None, face_detector_confidence=0.95,
                manipulation_probability=0.40, realism_probability=0.60, prediction_confidence=0.80, inference_latency_ms=10.0
            )
        ]
        track = FaceTrackSummary(
            tracking_id=0, frames_analyzed=1, first_timestamp=0.0, last_timestamp=0.0, duration_sec=0.0,
            mean_manipulation_probability=0.40, max_manipulation_probability=0.40, min_manipulation_probability=0.40,
            score_std=0.0, score_range=0.0, detection_coverage=1.0, detection_continuity=1.0,
            bbox_instability=0.0, landmark_instability=0.0, temporal_gaps=[], temporal_anomaly_score=58,
            observations=obs
        )
        windows, highest_risk = detector.detect_windows([track])
        self.assertGreater(len(windows), 0)
        temp_win = [w for w in windows if "TEMPORAL_ANOMALY" in w.trigger_types]
        self.assertEqual(len(temp_win), 1)
        self.assertEqual(temp_win[0].temporal_anomaly_score, 58)

    def test_05_tracking_discontinuity_evidence(self):
        """5. Verify evidence window triggered by face tracking gaps."""
        detector = EvidenceWindowDetector()
        obs = [
            TrackedFaceObservation(
                frame_index=0, timestamp_sec=0.0, face_id=0, tracking_id=0,
                bbox=(50, 50, 80, 80), landmarks=None, face_detector_confidence=0.95,
                manipulation_probability=0.30, realism_probability=0.70, prediction_confidence=0.80, inference_latency_ms=10.0
            ),
            TrackedFaceObservation(
                frame_index=90, timestamp_sec=3.0, face_id=0, tracking_id=0,
                bbox=(50, 50, 80, 80), landmarks=None, face_detector_confidence=0.95,
                manipulation_probability=0.30, realism_probability=0.70, prediction_confidence=0.80, inference_latency_ms=10.0
            )
        ]
        track = FaceTrackSummary(
            tracking_id=0, frames_analyzed=2, first_timestamp=0.0, last_timestamp=3.0, duration_sec=3.0,
            mean_manipulation_probability=0.30, max_manipulation_probability=0.30, min_manipulation_probability=0.30,
            score_std=0.0, score_range=0.0, detection_coverage=0.5, detection_continuity=0.0,
            bbox_instability=0.0, landmark_instability=0.0,
            temporal_gaps=[{"start_sec": 0.0, "end_sec": 3.0, "gap_duration_sec": 3.0}],
            temporal_anomaly_score=20, observations=obs
        )
        windows, highest_risk = detector.detect_windows([track])
        gap_win = [w for w in windows if "TRACKING_DISCONTINUITY" in w.trigger_types]
        self.assertEqual(len(gap_win), 1)

    def test_06_landmark_instability_evidence(self):
        """6. Verify evidence window triggered by excessive normalized landmark jitter."""
        detector = EvidenceWindowDetector(EvidenceWindowConfig(landmark_jitter_threshold=0.05))
        obs = [
            TrackedFaceObservation(
                frame_index=0, timestamp_sec=0.0, face_id=0, tracking_id=0,
                bbox=(100, 100, 100, 100),
                landmarks=[(120, 120), (160, 120), (140, 140), (130, 160), (150, 160)],
                face_detector_confidence=0.95, manipulation_probability=0.30,
                realism_probability=0.70, prediction_confidence=0.80, inference_latency_ms=10.0
            ),
            TrackedFaceObservation(
                frame_index=30, timestamp_sec=1.0, face_id=0, tracking_id=0,
                bbox=(100, 100, 100, 100),
                # Jitter landmark by 25 pixels
                landmarks=[(145, 120), (135, 120), (140, 165), (130, 135), (150, 135)],
                face_detector_confidence=0.95, manipulation_probability=0.30,
                realism_probability=0.70, prediction_confidence=0.80, inference_latency_ms=10.0
            )
        ]
        track = FaceTrackSummary(
            tracking_id=0, frames_analyzed=2, first_timestamp=0.0, last_timestamp=1.0, duration_sec=1.0,
            mean_manipulation_probability=0.30, max_manipulation_probability=0.30, min_manipulation_probability=0.30,
            score_std=0.0, score_range=0.0, detection_coverage=1.0, detection_continuity=1.0,
            bbox_instability=0.0, landmark_instability=0.35, temporal_gaps=[], temporal_anomaly_score=15,
            observations=obs
        )
        windows, highest_risk = detector.detect_windows([track])
        lm_win = [w for w in windows if "LANDMARK_INSTABILITY" in w.trigger_types]
        self.assertEqual(len(lm_win), 1)

    def test_07_event_clustering(self):
        """7. Verify clustering merges temporally adjacent events without duplicate windows."""
        detector = EvidenceWindowDetector(EvidenceWindowConfig(
            cluster_window_sec=2.0,
            high_probability_threshold=0.50,
            score_jump_threshold=0.20
        ))
        obs = [
            TrackedFaceObservation(
                frame_index=0, timestamp_sec=1.0, face_id=0, tracking_id=0,
                bbox=(50, 50, 80, 80), landmarks=None, face_detector_confidence=0.95,
                manipulation_probability=0.20, realism_probability=0.80, prediction_confidence=0.80, inference_latency_ms=10.0
            ),
            TrackedFaceObservation(
                frame_index=30, timestamp_sec=2.0, face_id=0, tracking_id=0,
                bbox=(50, 50, 80, 80), landmarks=None, face_detector_confidence=0.95,
                manipulation_probability=0.60, realism_probability=0.40, prediction_confidence=0.80, inference_latency_ms=10.0
            ),
            TrackedFaceObservation(
                frame_index=60, timestamp_sec=3.0, face_id=0, tracking_id=0,
                bbox=(50, 50, 80, 80), landmarks=None, face_detector_confidence=0.95,
                manipulation_probability=0.75, realism_probability=0.25, prediction_confidence=0.80, inference_latency_ms=10.0
            )
        ]
        track = FaceTrackSummary(
            tracking_id=0, frames_analyzed=3, first_timestamp=1.0, last_timestamp=3.0, duration_sec=2.0,
            mean_manipulation_probability=0.516, max_manipulation_probability=0.75, min_manipulation_probability=0.20,
            score_std=0.23, score_range=0.55, detection_coverage=1.0, detection_continuity=1.0,
            bbox_instability=0.0, landmark_instability=0.0, temporal_gaps=[], temporal_anomaly_score=20,
            observations=obs
        )
        windows, highest_risk = detector.detect_windows([track])
        # Because events at t=1.0->2.0 (jump) and t=2.0 (high) and t=3.0 (high) are within 2.0s cluster window,
        # they must merge into 1 unified evidence window
        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0].start_timestamp, 1.0)
        self.assertEqual(windows[0].end_timestamp, 3.0)
        self.assertIn("SUDDEN_SCORE_CHANGE", windows[0].trigger_types)
        self.assertIn("HIGH_MANIPULATION_PROBABILITY", windows[0].trigger_types)

    def test_08_evidence_window_duration(self):
        """8. Verify evidence window start, end, and duration calculations."""
        res = self.engine.analyze_video(SAMPLE_FACE_VIDEO)
        self.assertIn("evidence_windows", res)
        if res["evidence_windows"]:
            for ew in res["evidence_windows"]:
                self.assertGreaterEqual(ew["end_timestamp"], ew["start_timestamp"])
                self.assertGreater(ew["duration"], 0.0)
                self.assertEqual(ew["duration"], round(max(0.1, ew["end_timestamp"] - ew["start_timestamp"]), 2))

    def test_09_highest_risk_interval(self):
        """9. Verify highest-risk interval selection and ranking algorithm."""
        res = self.engine.analyze_video(SAMPLE_FACE_VIDEO)
        self.assertIn("highest_risk_interval", res)
        if res["evidence_windows"]:
            self.assertIsNotNone(res["highest_risk_interval"])
            hr = res["highest_risk_interval"]
            self.assertIn("evidence_id", hr)
            self.assertIn("ranking_score", hr)
            self.assertIn("peak_manipulation_probability", hr)
            self.assertIn("trigger_type", hr)
            max_rank = max(w["ranking_score"] for w in res["evidence_windows"])
            self.assertEqual(hr["ranking_score"], max_rank)

    def test_10_multiple_tracking_ids(self):
        """10. Verify evidence window generation across multiple distinct face tracks."""
        res = self.engine.analyze_video(MULTI_FACE_VIDEO)
        self.assertEqual(res["classification_status"], "ANALYZED")
        self.assertGreaterEqual(len(res["tracking_ids"]), 1)
        self.assertIn("score_sequences", res)
        self.assertIn("evidence_windows", res)

    def test_11_no_face_video(self):
        """11. Verify zero-face video produces ANALYZED_GENERAL_VIDEO and runs general temporal forensics without ViT."""
        res = self.engine.analyze_video(NO_FACE_VIDEO)
        self.assertEqual(res["classification_status"], "ANALYZED_GENERAL_VIDEO")
        self.assertIn(res["risk_level"], ["LOW RISK", "MEDIUM RISK", "HIGH RISK", "CRITICAL RISK"])
        self.assertEqual(res["evidence_source"], "VISUAL_GLOBAL")
        self.assertEqual(res["performance"]["vit_total_ms"], 0.0)

    def test_12_deterministic_evidence_generation(self):
        """12. Verify deterministic evidence windows and score sequences."""
        res1 = self.engine.analyze_video(SAMPLE_FACE_VIDEO)
        res2 = self.engine.analyze_video(SAMPLE_FACE_VIDEO)

        self.assertEqual(len(res1["evidence_windows"]), len(res2["evidence_windows"]))
        if res1["evidence_windows"]:
            self.assertEqual(
                res1["evidence_windows"][0]["ranking_score"],
                res2["evidence_windows"][0]["ranking_score"]
            )
            self.assertEqual(
                res1["highest_risk_interval"]["evidence_id"],
                res2["highest_risk_interval"]["evidence_id"]
            )

    def test_13_invalid_video(self):
        """13. Verify invalid video handling returns empty evidence windows."""
        fake_path = DATA_DIR / "invalid_video_9999.mp4"
        res = self.engine.analyze_video(fake_path)
        self.assertEqual(res["classification_status"], "ANALYSIS_ERROR")
        self.assertEqual(res["evidence_windows"], [])
        self.assertIsNone(res["highest_risk_interval"])

    def test_14_cleanup_of_temporary_frame_data(self):
        """14. Verify temporary workspace directories are cleanly removed after processing."""
        initial_tmp_count = 0
        with temporary_media_workspace() as tmp_dir:
            test_file = tmp_dir / "temp_probe.mp4"
            test_file.write_bytes(SAMPLE_FACE_VIDEO.read_bytes())
            res = self.engine.analyze_video(test_file)
            self.assertEqual(res["classification_status"], "ANALYZED")
            self.assertTrue(tmp_dir.exists())

        # Outside context manager, temporary directory must be cleaned up
        self.assertFalse(tmp_dir.exists())


if __name__ == "__main__":
    unittest.main()
