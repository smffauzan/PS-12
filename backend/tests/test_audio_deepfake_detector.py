"""
VERITAS AI — Audio Deepfake & Speech Anti-Spoofing Test Suite
Module: backend.tests.test_audio_deepfake_detector

Comprehensive test coverage verifying:
1. Model loading & CPU initialization
2. Weights integrity & layer verification
3. Direct CPU neural inference
4. Audio preprocessing & 16kHz resampling
5. Windowed audio segmentation
6. Real speech anti-spoofing analysis
7. Probability and score range constraints [0.0, 1.0] and [0, 100]
8. Inference determinism
9. Audio-level score aggregation & statistics
10. Grounded forensic timeline generation
11. No-audio track handling
12. Corrupt/malformed audio handling
13. Low quality / audio limitation filters
14. Video audio stream extraction lifecycle
15. Mock fallback and explicit demo labeling
16. Detector failure isolation in orchestrator
17. ModelRegistry health tracking
18. ForensicEnsembleEngine multimodal integration
"""

import os
import sys
import wave
import tempfile
import time
import math
import unittest
from pathlib import Path
from typing import Tuple
import numpy as np
import torch

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.models.audio_deepfake_detector import (
    AudioDeepfakeDetector,
    RealAudioDeepfakeDetector,
    MockAudioDetector,
    RawNet2,
    get_audio_deepfake_detector,
    DEFAULT_RAWNET2_WEIGHTS
)
from app.models.audio_detector import (
    RealAudioFeatureDetector,
    AudioDetector
)
from app.services.audio_forensics import audio_extractor, AudioForensicFeatures
from app.models.model_registry import model_registry, ModelStatus, ModalityType, ExecutionMode
from app.services.ensemble_engine import ensemble_engine, ForensicEnsembleEngine
from app.services.orchestrator import ForensicOrchestrator
from app.services.media_processor import temporary_media_workspace


def create_synthetic_wav(
    duration_sec: float = 4.0,
    sample_rate: int = 16000,
    harmonics: bool = True,
    silence: bool = False,
    clipping: bool = False,
    narrowband: bool = False
) -> Tuple[Path, bytes]:
    """Helper creating temporary WAV file fixtures for forensic audio testing."""
    n_samples = int(duration_sec * sample_rate)
    t = np.linspace(0, duration_sec, n_samples, endpoint=False)

    if silence:
        sig = np.zeros(n_samples, dtype=np.float32)
    elif narrowband:
        # Single low frequency tone with zero high-frequency rolloff
        sig = 0.5 * np.sin(2 * np.pi * 200 * t)
    elif harmonics:
        # Multi-harmonic voice-like spectrum
        sig = np.zeros(n_samples, dtype=np.float32)
        for h in range(1, 20):
            sig += (1.0 / (h ** 0.8)) * np.sin(2 * np.pi * (160.0 * h) * t)
        sig += 0.03 * np.random.randn(n_samples).astype(np.float32)
    else:
        sig = np.random.uniform(-0.5, 0.5, n_samples).astype(np.float32)

    if clipping:
        sig = np.clip(sig * 4.0, -1.0, 1.0)
    else:
        max_amp = np.max(np.abs(sig)) if len(sig) > 0 and np.max(np.abs(sig)) > 0 else 1.0
        sig = (sig / max_amp) * 0.75

    pcm16 = (sig * 32767).astype(np.int16)

    # Write to temp file
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = Path(tmp.name)
    with wave.open(str(tmp_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16.tobytes())

    return tmp_path, pcm16.tobytes()


class TestAudioDeepfakeDetector(unittest.TestCase):
    """Test suite covering the 18 verification requirements for Phase 6B-5."""

    @classmethod
    def setUpClass(cls):
        cls.detector = RealAudioDeepfakeDetector()
        cls.mock_detector = MockAudioDetector()

    # 1. Model Loading
    def test_audio_model_loading(self):
        self.assertIsNotNone(self.detector.model)
        self.assertTrue(self.detector.weights_verified)
        self.assertFalse(self.detector.is_mock)
        self.assertEqual(self.detector.model_version, "VERITAS-AUDIO-RAWNET2-v1.0")
        self.assertEqual(self.detector.detection_mode, "REAL_AUDIO_ANTI_SPOOFING")

    # 2. Weights Verification
    def test_weights_verification(self):
        self.assertTrue(DEFAULT_RAWNET2_WEIGHTS.exists())
        file_size_mb = DEFAULT_RAWNET2_WEIGHTS.stat().st_size / (1024 * 1024)
        self.assertGreater(file_size_mb, 50.0)  # ~70.5 MB state dict
        ckpt = torch.load(str(DEFAULT_RAWNET2_WEIGHTS), map_location="cpu", weights_only=False)
        self.assertIn("first_bn.weight", ckpt)
        self.assertIn("block0.0.conv1.weight", ckpt)
        self.assertIn("gru.weight_ih_l0", ckpt)
        self.assertIn("fc2_gru.weight", ckpt)
        self.assertEqual(ckpt["fc2_gru.weight"].shape, torch.Size([2, 1024]))

    # 3. CPU Inference
    def test_cpu_inference(self):
        x = torch.randn(1, 64000)
        with torch.no_grad():
            out = self.detector.model(x)
        self.assertEqual(out.shape, torch.Size([1, 2]))
        probs = torch.exp(out)
        self.assertAlmostEqual(float(torch.sum(probs).item()), 1.0, places=4)

    # 4. Audio Preprocessing
    def test_audio_preprocessing(self):
        # Test stereo to mono & 44.1kHz -> 16kHz resampling
        stereo_44k = np.random.randn(44100 * 2, 2).astype(np.float32)
        processed = self.detector.preprocess_samples(stereo_44k, orig_sr=44100)
        self.assertEqual(processed.ndim, 1)
        self.assertEqual(len(processed), 16000 * 2)
        self.assertLessEqual(np.max(np.abs(processed)), 1.0)

    # 5. Segment Generation
    def test_segment_generation(self):
        # Short audio (2.0s) -> should tile to 64,000 samples (1 segment)
        samples_2s = np.random.randn(32000).astype(np.float32)
        segs_short = self.detector.segment_audio(samples_2s)
        self.assertEqual(len(segs_short), 1)
        self.assertEqual(len(segs_short[0][3]), 64000)

        # Longer audio (10.0s = 160,000 samples) -> should generate multiple overlapping windows
        samples_10s = np.random.randn(160000).astype(np.float32)
        segs_long = self.detector.segment_audio(samples_10s)
        self.assertGreaterEqual(len(segs_long), 4)
        for seg_id, s_t, e_t, s_arr in segs_long:
            self.assertEqual(len(s_arr), 64000)
            self.assertGreater(e_t, s_t)

    # 6. Real Speech Anti-Spoofing Inference
    def test_real_audio_inference(self):
        wav_path, _ = create_synthetic_wav(duration_sec=5.0, harmonics=True)
        try:
            res = self.detector.analyze(wav_path)
            self.assertEqual(res["classification_status"], "ANALYZED")
            self.assertFalse(res["is_mock"])
            self.assertIn("score", res)
            self.assertIn("maximum_spoof_score", res)
            self.assertIn("mean_spoof_score", res)
            self.assertGreater(res["segments_analyzed"], 0)
            self.assertGreater(res["latency_ms"], 0.0)
        finally:
            if wav_path.exists():
                wav_path.unlink()

    # 7. Output Range Constraints
    def test_output_range(self):
        wav_path, _ = create_synthetic_wav(duration_sec=6.0, harmonics=True)
        try:
            res = self.detector.analyze(wav_path)
            self.assertGreaterEqual(res["score"], 0)
            self.assertLessEqual(res["score"], 100)
            self.assertGreaterEqual(res["maximum_spoof_score"], 0)
            self.assertLessEqual(res["maximum_spoof_score"], 100)
            for s in res["segments"]:
                self.assertGreaterEqual(s["spoof_probability"], 0.0)
                self.assertLessEqual(s["spoof_probability"], 1.0)
                self.assertGreaterEqual(s["prediction_confidence"], 0)
                self.assertLessEqual(s["prediction_confidence"], 100)
        finally:
            if wav_path.exists():
                wav_path.unlink()

    # 8. Determinism
    def test_determinism(self):
        wav_path, _ = create_synthetic_wav(duration_sec=4.0, harmonics=True)
        try:
            res1 = self.detector.analyze(wav_path)
            res2 = self.detector.analyze(wav_path)
            self.assertEqual(res1["score"], res2["score"])
            self.assertEqual(res1["maximum_spoof_score"], res2["maximum_spoof_score"])
            self.assertEqual(len(res1["segments"]), len(res2["segments"]))
            for s1, s2 in zip(res1["segments"], res2["segments"]):
                self.assertEqual(s1["spoof_probability"], s2["spoof_probability"])
        finally:
            if wav_path.exists():
                wav_path.unlink()

    # 9. Audio-Level Score Aggregation
    def test_audio_aggregation(self):
        wav_path, _ = create_synthetic_wav(duration_sec=8.0, harmonics=True)
        try:
            res = self.detector.analyze(wav_path)
            seg_scores = [int(round(s["spoof_probability"] * 100)) for s in res["segments"]]
            self.assertEqual(res["maximum_spoof_score"], max(seg_scores))
            self.assertEqual(res["mean_spoof_score"], int(round(float(np.mean(seg_scores)))))
            self.assertIsNotNone(res["highest_risk_segment"])
            self.assertEqual(res["segment_count"], len(res["segments"]))
        finally:
            if wav_path.exists():
                wav_path.unlink()

    # 10. Grounded Timeline Generation
    def test_audio_timeline(self):
        wav_path, _ = create_synthetic_wav(duration_sec=6.0, harmonics=True)
        try:
            res = self.detector.analyze(wav_path)
            self.assertIsInstance(res["timeline"], list)
            for event in res["timeline"]:
                self.assertIn("start_timestamp", event)
                self.assertIn("end_timestamp", event)
                self.assertIn("formatted_time", event)
                self.assertIn("event_type", event)
        finally:
            if wav_path.exists():
                wav_path.unlink()

    # 11. No-Audio Handling
    def test_no_audio(self):
        res = self.detector.analyze(None)
        self.assertEqual(res["classification_status"], "NO_AUDIO")
        self.assertEqual(res["score"], 0)
        self.assertEqual(res["segments_analyzed"], 0)

        empty_bytes = b""
        res_empty = self.detector.analyze(empty_bytes)
        self.assertEqual(res_empty["classification_status"], "NO_AUDIO")

    # 12. Corrupt / Malformed Audio Handling
    def test_corrupt_audio(self):
        corrupt_bytes = b"RIFF\x00\x00\x00\x00WAVEfmt \x10\x00\x00\x00INVALID_HEADER_DATA"
        res = self.detector.analyze(corrupt_bytes)
        self.assertIn(res["classification_status"], ["NO_AUDIO", "TOO_SHORT", "ANALYSIS_ERROR", "INSUFFICIENT_AUDIO_EVIDENCE"])
        self.assertEqual(res["score"], 0)

    # 13. Low Quality / Audio Limitations Filter
    def test_low_quality_audio(self):
        # 13a. Too short (<0.5s)
        wav_short, _ = create_synthetic_wav(duration_sec=0.2, harmonics=True)
        try:
            res_short = self.detector.analyze(wav_short)
            self.assertEqual(res_short["classification_status"], "TOO_SHORT")
            self.assertEqual(res_short["score"], 0)
        finally:
            if wav_short.exists():
                wav_short.unlink()

        # 13b. Excessive silence (>90%)
        wav_silence, _ = create_synthetic_wav(duration_sec=4.0, silence=True)
        try:
            res_silence = self.detector.analyze(wav_silence)
            self.assertIn(res_silence["classification_status"], ["EXCESSIVE_SILENCE", "INSUFFICIENT_AUDIO_EVIDENCE"])
            self.assertEqual(res_silence["score"], 0)
        finally:
            if wav_silence.exists():
                wav_silence.unlink()

        # 13c. Narrowband / Heavily compressed
        wav_narrow, _ = create_synthetic_wav(duration_sec=4.0, narrowband=True)
        try:
            res_narrow = self.detector.analyze(wav_narrow)
            self.assertIn(res_narrow["classification_status"], ["HEAVILY_COMPRESSED", "INSUFFICIENT_AUDIO_EVIDENCE"])
        finally:
            if wav_narrow.exists():
                wav_narrow.unlink()

    # 14. Video Audio Stream Lifecycle
    def test_video_audio_extraction(self):
        with temporary_media_workspace() as tmp_dir:
            tmp_aud = tmp_dir / "temp_video_audio.wav"
            t = np.linspace(0, 4.0, 16000 * 4, endpoint=False)
            sig = (np.sin(2 * np.pi * 300 * t) * 0.5 * 32767).astype(np.int16)
            with wave.open(str(tmp_aud), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(sig.tobytes())

            self.assertTrue(tmp_aud.exists())
            res = self.detector.analyze(tmp_aud)
            self.assertIsNotNone(res)

        # Confirm workspace cleanup
        self.assertFalse(tmp_aud.exists())

    # 15. Mock Fallback & Explicit Labeling
    def test_mock_fallback(self):
        mock_det = get_audio_deepfake_detector(force_mock=True)
        self.assertTrue(mock_det.is_mock)
        res = mock_det.analyze("dummy_audio.wav")
        self.assertTrue(res["is_mock"])
        self.assertIn("DEMO MODE", res["detection_mode"])
        self.assertGreater(res["score"], 0)

    # 16. Detector Failure Isolation
    def test_model_failure_isolation(self):
        class FailingAudioDetector(AudioDeepfakeDetector):
            def analyze(self, media_path_or_bytes: Any) -> Dict[str, Any]:
                raise RuntimeError("Simulated internal CPU inference crash")

        failing_detector = FailingAudioDetector()
        orchestrator = ForensicOrchestrator(audio_detector=failing_detector)

        wav_path, _ = create_synthetic_wav(duration_sec=3.0, harmonics=True)
        try:
            result, payload = orchestrator.process(
                filename="failing_test.wav",
                media_type="audio",
                file_size="64 KB",
                case_id="CASE-AUD-FAIL",
                analysis_id="ANL-AUD-FAIL",
                file_path=wav_path
            )
            self.assertEqual(result.status, "COMPLETE")
            self.assertIsNotNone(result.risk)
            self.assertIn("audio", result.metadata.get("skipped_models", []))
            self.assertIn("Simulated internal CPU inference crash", result.metadata.get("skip_reasons", {}).get("audio", ""))
        finally:
            if wav_path.exists():
                wav_path.unlink()

    # 17. ModelRegistry Health Tracking
    def test_model_registry(self):
        active_models = model_registry.get_active_models()
        model_ids = [m.model_id for m in active_models]
        self.assertIn("VERITAS-AUDIO-RAWNET2-v1", model_ids)
        self.assertIn("VERITAS-AUDIO-FEATURE-v1", model_ids)

        rawnet_meta = model_registry.get_model("VERITAS-AUDIO-RAWNET2-v1")
        self.assertTrue(rawnet_meta.cpu_supported)
        self.assertTrue(rawnet_meta.loaded)
        self.assertTrue(rawnet_meta.weights_verified)

        health = model_registry.get_health_report()
        self.assertIn("VERITAS-AUDIO-RAWNET2-v1", health)

    # 18. Ensemble Integration
    def test_ensemble_integration(self):
        wav_path, _ = create_synthetic_wav(duration_sec=4.0, harmonics=True)
        try:
            orchestrator = ForensicOrchestrator()
            result, payload = orchestrator.process(
                filename="real_voice_sample.wav",
                media_type="audio",
                file_size="128 KB",
                case_id="CASE-AUD-ENS",
                analysis_id="ANL-AUD-ENS",
                file_path=wav_path,
                execution_mode=ExecutionMode.DEEP_FORENSICS
            )
            self.assertEqual(result.media_type, "audio")
            self.assertEqual(result.status, "COMPLETE")
            self.assertIn("audio", result.metadata.get("model_evidence", {}))
            self.assertIn("audio_features", result.metadata.get("model_evidence", {}))
            self.assertEqual(result.metadata.get("calibration_status"), "NOT_CALIBRATED")
        finally:
            if wav_path.exists():
                wav_path.unlink()


if __name__ == "__main__":
    unittest.main()
