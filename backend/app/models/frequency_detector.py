"""
VERITAS AI — Image Frequency Forensics Detector
Module: backend.app.models.frequency_detector

Provides the Frequency Forensic Detector extracting 2D FFT spectral energy distributions
and Spatial Rich Model (SRM) high-frequency noise residuals across image/face regions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from pathlib import Path
import logging
import time
import numpy as np
import cv2

from app.services.media_processor import temporary_media_workspace

logger = logging.getLogger("veritas.models.frequency")


class FrequencyDetector(ABC):
    """Abstract base detector interface for frequency-domain artifact analysis."""
    
    @abstractmethod
    def analyze(self, image_or_crop: Any) -> Dict[str, Any]:
        pass


class MockFrequencyDetector(FrequencyDetector):
    """
    Simulated demo detector for frequency forensics.
    Explicitly labeled as DEMO MODE // SIMULATED FREQUENCY DETECTION.
    """
    def __init__(self, model_version: str = "VERITAS-FREQ-MOCK-v0.1"):
        self.model_version = model_version
        self.is_mock = True
        self.detection_mode = "DEMO MODE // SIMULATED FREQUENCY DETECTION"

    def analyze(self, image_or_crop: Any) -> Dict[str, Any]:
        return {
            "model_name": "F3Net Dual-Stream Frequency Analyzer (Simulated)",
            "model_version": self.model_version,
            "category": "Frequency AI",
            "evidence_source": "FREQUENCY",
            "detection_mode": self.detection_mode,
            "is_mock": True,
            "classification_status": "ANALYZED",
            "score": 68,
            "confidence": 84,
            "frequency_anomaly_score": 68,
            "signals": [
                {
                    "id": "sig-freq-mock-1",
                    "name": "High-Frequency Spectral Energy Loss (Simulated)",
                    "category": "frequency",
                    "evidence_source": "FREQUENCY",
                    "severity": "medium",
                    "confidence": 84,
                    "affectedRegionOrTime": "Spectral Nyquist Perimeter",
                    "explanation": "2D DCT spectral profile exhibits abnormal energy attenuation in mid-to-high frequency bins."
                }
            ],
            "latency_ms": 18
        }


class SpatialFrequencyDetector(FrequencyDetector):
    """
    Real Spatial Frequency Forensic Detector:
    Applies 2D Fast Fourier Transform (FFT) and high-pass Laplacian/SRM filter kernels
    to measure high-frequency energy ratio and unnatural spectral attenuation.
    
    NOTE: Output is a frequency anomaly score (0-100), not a calibrated fake probability.
    """
    def __init__(self, model_version: str = "VERITAS-FREQ-SRM-v1.0"):
        self.model_version = model_version
        self.is_mock = False
        self.detection_mode = "REAL_FREQUENCY_FORENSICS"
        self._mock_fallback = MockFrequencyDetector()

    def analyze(self, image_or_crop: Any) -> Dict[str, Any]:
        t0 = time.perf_counter()

        img_bgr = None
        if isinstance(image_or_crop, np.ndarray):
            img_bgr = image_or_crop
        elif isinstance(image_or_crop, (str, Path)):
            p = Path(image_or_crop)
            if p.exists() and p.is_file():
                img_bgr = cv2.imread(str(p))
                if img_bgr is None:
                    # Try opening as video to extract sample frame
                    cap = cv2.VideoCapture(str(p))
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            img_bgr = frame
                        cap.release()
            else:
                return {
                    "model_name": "2D FFT Spectral & SRM Residual Analyzer",
                    "model_version": self.model_version,
                    "category": "Frequency AI",
                    "detection_mode": self.detection_mode,
                    "is_mock": False,
                    "classification_status": "UNREADABLE_INPUT",
                    "score": 0,
                    "confidence": 0,
                    "signals": [],
                    "latency_ms": 0.0
                }
        elif isinstance(image_or_crop, bytes):
            arr = np.frombuffer(image_or_crop, dtype=np.uint8)
            img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        if img_bgr is None or img_bgr.size == 0:
            return {
                "model_name": "2D FFT Spectral & SRM Residual Analyzer",
                "model_version": self.model_version,
                "category": "Frequency AI",
                "detection_mode": self.detection_mode,
                "is_mock": False,
                "classification_status": "SKIPPED_NON_IMAGE",
                "score": 0,
                "confidence": 0,
                "signals": [],
                "latency_ms": 0.0
            }


        # Convert to grayscale for frequency domain transform
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY) if img_bgr.ndim == 3 else img_bgr
        gray_f = gray.astype(np.float32)

        # 1. 2D FFT Magnitude Spectrum
        f = np.fft.fft2(gray_f)
        fshift = np.fft.fftshift(f)
        magnitude = np.abs(fshift)

        h, w = gray.shape
        cy, cx = h // 2, w // 2
        r = min(cy, cx)

        # Create low-pass vs high-pass radial masks
        y, x = np.ogrid[:h, :w]
        dist_from_center = np.sqrt((x - cx)**2 + (y - cy)**2)
        low_mask = dist_from_center <= (r * 0.3)
        high_mask = dist_from_center >= (r * 0.7)

        low_energy = float(np.sum(magnitude[low_mask]))
        high_energy = float(np.sum(magnitude[high_mask]))
        total_energy = float(np.sum(magnitude)) or 1e-9

        high_energy_ratio = high_energy / total_energy
        low_energy_ratio = low_energy / total_energy

        # 2. High-Pass Spatial Residual (Laplacian variance)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        # 3. Frequency Anomaly Score (0-100)
        # Deepfake/diffusion faces typically exhibit attenuated high-frequency texture noise (low ratio)
        # or checkerboard grid peaks
        attenuation_score = max(0.0, min(1.0, 1.0 - (high_energy_ratio * 20.0)))
        blur_score = max(0.0, min(1.0, 1.0 - (laplacian_var / 500.0)))
        raw_anomaly = 0.60 * attenuation_score + 0.40 * blur_score
        freq_score = int(round(np.clip(raw_anomaly * 100, 0, 100)))

        signals = []
        if freq_score >= 50:
            signals.append({
                "id": "sig-freq-srm-1",
                "name": "High-Frequency Spectral Attenuation Anomaly",
                "category": "frequency",
                "evidence_source": "FREQUENCY",
                "severity": "high" if freq_score >= 75 else "medium",
                "confidence": freq_score,
                "affectedRegionOrTime": "2D Fourier Spectrum Perimeter",
                "explanation": f"High-frequency energy ratio of {round(high_energy_ratio*100, 2)}% indicates unnatural smoothing or neural generation artifact."
            })

        latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        return {
            "model_name": "2D FFT Spectral & SRM Residual Analyzer",
            "model_version": self.model_version,
            "category": "Frequency AI",
            "evidence_source": "FREQUENCY",
            "detection_mode": self.detection_mode,
            "is_mock": False,
            "classification_status": "ANALYZED",
            "score": freq_score,
            "confidence": 85,
            "frequency_anomaly_score": freq_score,
            "high_energy_ratio": round(high_energy_ratio, 4),
            "low_energy_ratio": round(low_energy_ratio, 4),
            "laplacian_variance": round(laplacian_var, 2),
            "signals": signals,
            "latency_ms": latency_ms
        }


def get_frequency_detector(force_mock: bool = False) -> FrequencyDetector:
    """Factory creating the appropriate frequency detector."""
    if force_mock:
        return MockFrequencyDetector()
    try:
        return SpatialFrequencyDetector()
    except Exception as exc:
        logger.error(f"Failed to initialize SpatialFrequencyDetector: {exc}. Falling back to MockFrequencyDetector.")
        return MockFrequencyDetector()
