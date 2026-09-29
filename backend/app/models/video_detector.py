"""
VERITAS AI — Real Video Detector
Module: backend.app.models.video_detector

Provides the Real OpenCV YuNet + ViT Frame-Level Video Forensic Detector,
with backward-compatible abstract interface and Mock fallback.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from pathlib import Path
import logging

from app.services.video_forensics import video_forensic_engine, RealVideoForensicEngine, VideoSamplingConfig
from app.services.media_processor import temporary_media_workspace

logger = logging.getLogger("veritas.models.video")

class VideoDetector(ABC):
    """Abstract base detector interface for video-level forensic processing."""
    
    @abstractmethod
    def analyze(self, media_path_or_bytes: Any) -> Dict[str, Any]:
        pass


class MockVideoDetector(VideoDetector):
    """
    Simulated demo detector for video forensics.
    Explicitly labeled as DEMO MODE // SIMULATED VIDEO DETECTION.
    """
    def __init__(self, model_version: str = "VERITAS-VIDEO-MOCK-v0.1"):
        self.model_version = model_version
        self.is_mock = True
        self.detection_mode = "DEMO MODE // SIMULATED VIDEO DETECTION"

    def analyze(self, media_path_or_bytes: Any) -> Dict[str, Any]:
        return {
            "model_name": "Video Spatial & Facial Warp Detector (Simulated)",
            "model_version": self.model_version,
            "category": "Visual AI",
            "detection_mode": self.detection_mode,
            "is_mock": True,
            "classification_status": "ANALYZED",
            "score": 91,
            "confidence": 93,
            "frame_level_max_risk": 0.91,
            "frame_level_mean_risk": 0.74,
            "temporal_anomaly_score": 68,
            "signals": [
                {
                    "id": "sig-vid-mock-1",
                    "name": "Face Boundary Blending Artifact (Simulated)",
                    "category": "visual",
                    "severity": "high",
                    "confidence": 91,
                    "affectedRegionOrTime": "Jawline & Neck Perimeter [00:21.00]",
                    "explanation": "Gradient discontinuity along the mask boundary indicates neural warping and edge blending."
                }
            ],
            "timeline": [],
            "latency_ms": 42
        }


class RealVideoDetector(VideoDetector):
    """
    Real Video Forensic Detector:
    Decodes video frames using OpenCV (without loading whole video into RAM),
    runs real OpenCV YuNet face detection on sampled frames,
    tracks faces with SimpleFaceTracker across frames,
    and runs real ViT deepfake classifier ONNX on face crops.
    """
    def __init__(
        self,
        engine: Optional[RealVideoForensicEngine] = None,
        sampling_config: Optional[VideoSamplingConfig] = None
    ):
        self.engine = engine or video_forensic_engine
        self.sampling_config = sampling_config or VideoSamplingConfig()
        self.model_version = "VERITAS-VIDEO-REAL-v1.0"
        self.is_mock = False
        self.detection_mode = "REAL_AI_VIDEO"
        self._mock_fallback = MockVideoDetector()

    def analyze(self, media_path_or_bytes: Any) -> Dict[str, Any]:
        # 1. Path or String Path
        if isinstance(media_path_or_bytes, (str, Path)):
            p = Path(media_path_or_bytes)
            if p.exists() and p.is_file():
                result = self.engine.analyze_video(p, sampling_config=self.sampling_config)
                result["model_name"] = "OpenCV YuNet + ViT Frame-Level Video Forensic Engine"
                result["model_version"] = self.model_version
                result["category"] = "Visual AI"
                return result
            else:
                return {
                    "classification_status": "ANALYSIS_ERROR",
                    "detection_mode": "REAL_AI_VIDEO",
                    "is_mock": False,
                    "error": f"VIDEO_FILE_NOT_FOUND: Video file not accessible at '{media_path_or_bytes}'.",
                    "risk_level": "INCONCLUSIVE",
                    "score": None,
                    "confidence": 0,
                    "evidence_windows": [],
                    "highest_risk_interval": None,
                    "score_sequences": {},
                    "tracks": [],
                    "timeline": [],
                    "signals": [],
                    "limitations": TEMPORAL_LIMITATIONS,
                    "latency_ms": 0.0
                }

        # 2. Raw Bytes Ingestion
        elif isinstance(media_path_or_bytes, bytes):
            with temporary_media_workspace() as tmp_dir:
                tmp_file = tmp_dir / "input_video.mp4"
                tmp_file.write_bytes(media_path_or_bytes)
                result = self.engine.analyze_video(tmp_file, sampling_config=self.sampling_config)
                result["model_name"] = "OpenCV YuNet + ViT Frame-Level Video Forensic Engine"
                result["model_version"] = self.model_version
                result["category"] = "Visual AI"
                return result

        else:
            return {
                "classification_status": "ANALYSIS_ERROR",
                "detection_mode": "REAL_AI_VIDEO",
                "is_mock": False,
                "error": f"INVALID_MEDIA_TYPE: Unsupported video input type '{type(media_path_or_bytes)}'.",
                "risk_level": "INCONCLUSIVE",
                "score": None,
                "confidence": 0,
                "evidence_windows": [],
                "highest_risk_interval": None,
                "score_sequences": {},
                "tracks": [],
                "timeline": [],
                "signals": [],
                "limitations": TEMPORAL_LIMITATIONS,
                "latency_ms": 0.0
            }


def get_video_detector(force_mock: bool = False) -> VideoDetector:
    """Factory creating the appropriate video detector."""
    if force_mock:
        return MockVideoDetector()
    try:
        return RealVideoDetector()
    except Exception as exc:
        logger.error(f"Failed to initialize RealVideoDetector: {exc}")
        return RealVideoDetector()
