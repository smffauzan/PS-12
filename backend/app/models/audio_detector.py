"""
VERITAS AI — Audio Forensic Detector Architecture
Module: backend.app.models.audio_detector

Provides the Real Audio Feature Extractor and Mock Audio Detector fallback.
Extracts measurable physical audio properties (RMS, ZCR, spectral centroid, rolloff, F0, MFCC)
and emits structured forensic signals.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from pathlib import Path
import logging
import time

from app.services.audio_forensics import audio_extractor, AudioForensicFeatures
from app.services.media_processor import temporary_media_workspace

logger = logging.getLogger("veritas.models.audio")


class AudioDetector(ABC):
    """Abstract base detector interface for audio synthesis & voice cloning."""
    
    @abstractmethod
    def analyze(self, media_path_or_bytes: Any) -> Dict[str, Any]:
        pass


class MockAudioDetector(AudioDetector):
    """
    Simulated demo detector for speech forensics.
    Explicitly labeled as DEMO MODE // SIMULATED AUDIO DETECTION.
    """
    def __init__(self, model_version: str = "VERITAS-AUDIO-MOCK-v0.1"):
        self.model_version = model_version
        self.is_mock = True
        self.detection_mode = "DEMO MODE // SIMULATED AUDIO DETECTION"

    def analyze(self, media_path_or_bytes: Any) -> Dict[str, Any]:
        return {
            "model_name": "Wav2Vec2 + Mel Vocoder Authenticator (Simulated)",
            "model_version": self.model_version,
            "category": "Audio AI",
            "evidence_source": "AUDIO_GENERAL",
            "detection_mode": self.detection_mode,
            "is_mock": True,
            "classification_status": "ANALYZED",
            "score": 73,
            "confidence": 88,
            "signals": [
                {
                    "id": "sig-aud-mock-1",
                    "name": "Audio Spectral Formant Anomaly (Simulated)",
                    "category": "audio",
                    "evidence_source": "AUDIO_GENERAL",
                    "severity": "medium",
                    "confidence": 85,
                    "affectedRegionOrTime": "3.8kHz - 5.2kHz Band [00:07.30]",
                    "explanation": "Unnatural linear phase coherence across upper harmonic formants typical of neural vocoders."
                },
                {
                    "id": "sig-aud-mock-2",
                    "name": "Neural Voice Synthesis Indicator (Simulated)",
                    "category": "audio",
                    "evidence_source": "AUDIO_GENERAL",
                    "severity": "high",
                    "confidence": 88,
                    "affectedRegionOrTime": "Voice Track [00:06 - 00:18]",
                    "explanation": "Mel-spectrogram zero-crossing distribution matches acoustic footprint of diffusion voice cloning."
                }
            ],
            "latency_ms": 29
        }


class RealAudioFeatureDetector(AudioDetector):
    """
    Real Audio Forensic Detector:
    Extracts measurable physical and spectral features (RMS, ZCR, spectral centroid,
    bandwidth, rolloff, MFCCs, F0 pitch) from audio files or waveforms.
    
    NOTE: Outputs represent acoustic forensic measurements, not deepfake probabilities.
    """
    def __init__(self, model_version: str = "VERITAS-AUDIO-FEATURE-v1.0"):
        self.model_version = model_version
        self.is_mock = False
        self.detection_mode = "REAL_AUDIO_FORENSICS"
        self._mock_fallback = MockAudioDetector()

    def analyze(self, media_path_or_bytes: Any) -> Dict[str, Any]:
        t0 = time.perf_counter()
        
        # Check if dummy filename without real file
        if isinstance(media_path_or_bytes, (str, Path)):
            p = Path(media_path_or_bytes)
            if not p.exists() or not p.is_file():
                logger.info(f"Audio file '{media_path_or_bytes}' not found. Falling back to MockAudioDetector.")
                return self._mock_fallback.analyze(media_path_or_bytes)

        samples, sr, ch = audio_extractor.read_audio_file(media_path_or_bytes)
        features = audio_extractor.extract_from_pcm(samples, sr, ch)
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        if features.total_samples == 0 or features.duration_sec < 0.3:
            return {
                "model_name": "Physical Acoustic & Spectral Domain Audio Analyzer",
                "model_version": self.model_version,
                "category": "Audio AI",
                "evidence_source": "AUDIO_GENERAL",
                "detection_mode": self.detection_mode,
                "is_mock": False,
                "classification_status": "NO_AUDIO" if features.total_samples == 0 else "TOO_SHORT",
                "score": 0,
                "confidence": 0,
                "audio_forensic_features": features.to_dict(),
                "signals": [],
                "latency_ms": latency_ms
            }

        if features.rms_energy < 1e-4 or features.silence_ratio >= 0.95:
            return {
                "model_name": "Physical Acoustic & Spectral Domain Audio Analyzer",
                "model_version": self.model_version,
                "category": "Audio AI",
                "evidence_source": "AUDIO_GENERAL",
                "detection_mode": self.detection_mode,
                "is_mock": False,
                "classification_status": "EXCESSIVE_SILENCE",
                "score": 0,
                "confidence": 0,
                "audio_forensic_features": features.to_dict(),
                "signals": [],
                "latency_ms": latency_ms
            }

        signals = []
        if features.clipping_ratio > 0.05:
            signals.append({
                "id": "sig-aud-clip-1",
                "name": "Acoustic Signal Amplitude Clipping",
                "category": "audio",
                "evidence_source": "AUDIO_GENERAL",
                "severity": "medium",
                "confidence": int(round(features.clipping_ratio * 100)),
                "affectedRegionOrTime": f"Audio Stream (0.0s - {features.duration_sec:.1f}s)",
                "explanation": f"High amplitude clipping observed in {round(features.clipping_ratio*100, 1)}% of samples."
            })
        if features.spectral_rolloff_hz < 3000 and features.duration_sec > 0.5:
            signals.append({
                "id": "sig-aud-bandwidth-1",
                "name": "Narrowband Frequency Cutoff Artifact",
                "category": "audio",
                "evidence_source": "AUDIO_GENERAL",
                "severity": "low",
                "confidence": 75,
                "affectedRegionOrTime": "High Frequency Spectrum (>3.0kHz)",
                "explanation": f"Spectral rolloff is constrained at {features.spectral_rolloff_hz:.0f}Hz, typical of resampled or synthesized audio."
            })

        # Calculate heuristic acoustic anomaly indicator (0-100)
        anomaly_indicator = min(100, int(round((features.clipping_ratio * 40) + (1.0 - min(1.0, features.spectral_rolloff_hz / 8000.0)) * 30 + (features.silence_ratio * 20))))

        return {
            "model_name": "Physical Acoustic & Spectral Domain Audio Analyzer",
            "model_version": self.model_version,
            "category": "Audio AI",
            "evidence_source": "AUDIO_GENERAL",
            "detection_mode": self.detection_mode,
            "is_mock": False,
            "classification_status": "ANALYZED",
            "score": anomaly_indicator,
            "confidence": 80,
            "audio_forensic_features": features.to_dict(),
            "signals": signals,
            "latency_ms": latency_ms
        }


def get_audio_detector(force_mock: bool = False) -> AudioDetector:
    """Factory creating the appropriate audio detector."""
    if force_mock:
        return MockAudioDetector()
    try:
        return RealAudioFeatureDetector()
    except Exception as exc:
        logger.error(f"Failed to initialize RealAudioFeatureDetector: {exc}. Falling back to MockAudioDetector.")
        return MockAudioDetector()
