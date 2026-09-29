"""
VERITAS AI — Content-Agnostic Global Visual Forensics Engine
Module: backend.app.services.global_visual_forensics

Provides content-agnostic spatial texture, noise residual, and compression artifact
analysis for any visual media (human, non-human, landscapes, AI artwork, buildings,
products, illustrations, screenshots). Operates independently of facial presence.
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
import time
import numpy as np
import cv2
import logging

logger = logging.getLogger("veritas.forensics.global_visual")


class GlobalVisualForensics:
    """
    Content-Agnostic Image and Frame Forensic Analyzer.
    Analyzes:
    1. Spatial texture & gradient variance distribution
    2. Local noise residual uniformity
    3. 8x8 block boundary compression consistency
    4. Chrominance & color gradient smoothness
    
    NOTE: Outputs represent physical and statistical forensic measurements.
    """

    def __init__(self, model_version: str = "VERITAS-VISION-GLOBAL-v1.0"):
        self.model_version = model_version
        self.model_name = "Global Spatial & Texture Forensic Analyzer"
        self.is_mock = False
        self.detection_mode = "REAL_GLOBAL_VISUAL_FORENSICS"

    def analyze(self, image_input: Any) -> Dict[str, Any]:
        """
        Analyzes an RGB/BGR numpy array, image file path, or bytes.
        """
        t0 = time.perf_counter()
        img = self._load_image(image_input)
        if img is None or img.size == 0:
            return {
                "model_name": self.model_name,
                "model_version": self.model_version,
                "category": "Visual AI",
                "detection_mode": self.detection_mode,
                "is_mock": False,
                "evidence_source": "VISUAL_GLOBAL",
                "classification_status": "SKIPPED_UNREADABLE",
                "score": 0,
                "confidence": 0,
                "signals": [],
                "latency_ms": 0.0
            }

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img

        # 1. Texture & Gradient Variance (Laplacian & Sobel)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        lap_var = float(laplacian.var())
        
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        grad_mag = np.sqrt(sobel_x**2 + sobel_y**2)
        grad_var = float(grad_mag.var())

        # 2. Local Noise Residual Uniformity
        # Natural sensor images exhibit Gaussian noise with spatial variance;
        # Generative diffusion/GAN images frequently exhibit oversmoothed regions or uniform synthetic residuals.
        blurred = cv2.GaussianBlur(gray, (5, 5), 1.0)
        noise_residual = np.abs(gray.astype(np.float32) - blurred.astype(np.float32))
        
        # Partition into 16x16 grid to compute local noise variance distribution
        grid_size = 16
        block_h, block_w = max(4, h // grid_size), max(4, w // grid_size)
        local_noise_vars = []
        for i in range(grid_size):
            for j in range(grid_size):
                block = noise_residual[i*block_h:(i+1)*block_h, j*block_w:(j+1)*block_w]
                if block.size > 0:
                    local_noise_vars.append(float(np.var(block)))

        noise_dispersion = float(np.std(local_noise_vars) / (np.mean(local_noise_vars) + 1e-6)) if local_noise_vars else 1.0

        # 3. 8x8 DCT Blocking Discontinuity (JPEG Compression Consistency)
        # Measures whether 8x8 grid boundary gradients match internal block gradients
        h_trim, w_trim = (h // 8) * 8, (w // 8) * 8
        if h_trim >= 32 and w_trim >= 32:
            cropped = gray[:h_trim, :w_trim].astype(np.float32)
            # Boundary differences (every 8th pixel: row/col 7 to 8, 15 to 16, etc.)
            diff_h = np.abs(cropped[7:h_trim-1:8, :] - cropped[8:h_trim:8, :]) if h_trim > 8 else np.array([0.0])
            diff_w = np.abs(cropped[:, 7:w_trim-1:8] - cropped[:, 8:w_trim:8]) if w_trim > 8 else np.array([0.0])
            boundary_diff = float((np.mean(diff_h) + np.mean(diff_w)) / 2.0)
            
            # Non-boundary internal sample (row/col 3 to 4, 11 to 12, etc.)
            int_diff_h = np.abs(cropped[3:h_trim-1:8, :] - cropped[4:h_trim:8, :]) if h_trim > 8 else np.array([0.0])
            int_diff_w = np.abs(cropped[:, 3:w_trim-1:8] - cropped[:, 4:w_trim:8]) if w_trim > 8 else np.array([0.0])
            internal_diff = float((np.mean(int_diff_h) + np.mean(int_diff_w)) / 2.0)
            
            blocking_ratio = float(boundary_diff / (internal_diff + 1e-6))
        else:
            blocking_ratio = 1.0

        # 4. Compute Normalized Global Visual Anomaly Score (0 - 100)
        # Low noise dispersion (< 0.25) or abnormal blur/smoothing indicates synthetic generation artifacts
        smoothing_anomaly = max(0.0, min(1.0, (1.0 - min(1.0, lap_var / 400.0))))
        noise_uniformity_anomaly = max(0.0, min(1.0, 1.0 - min(1.0, noise_dispersion / 1.5)))
        blocking_anomaly = max(0.0, min(1.0, abs(blocking_ratio - 1.0) * 0.8))

        raw_visual_anomaly = (
            0.40 * smoothing_anomaly +
            0.40 * noise_uniformity_anomaly +
            0.20 * blocking_anomaly
        )
        visual_score = int(round(np.clip(raw_visual_anomaly * 100, 0, 100)))
        confidence = 85

        signals = []
        if smoothing_anomaly >= 0.70:
            signals.append({
                "id": "sig-vis-smooth-1",
                "name": "Global Spatial Smoothing & Texture Loss",
                "category": "visual",
                "evidence_source": "VISUAL_GLOBAL",
                "severity": "medium",
                "confidence": int(round(smoothing_anomaly * 100)),
                "affectedRegionOrTime": "Full Image Surface",
                "explanation": f"Spatial gradient variance ({round(lap_var, 1)}) indicates significant texture loss or neural diffusion smoothing."
            })
        if noise_uniformity_anomaly >= 0.75:
            signals.append({
                "id": "sig-vis-noise-1",
                "name": "Atypical Noise Residual Distribution",
                "category": "visual",
                "evidence_source": "VISUAL_GLOBAL",
                "severity": "medium",
                "confidence": int(round(noise_uniformity_anomaly * 100)),
                "affectedRegionOrTime": "Sensor Residual Field",
                "explanation": "Local noise residual distribution lacks characteristic physical camera sensor noise patterns."
            })

        latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "category": "Visual AI",
            "evidence_source": "VISUAL_GLOBAL",
            "detection_mode": self.detection_mode,
            "is_mock": False,
            "classification_status": "ANALYZED",
            "score": visual_score,
            "confidence": confidence,
            "texture_variance": round(lap_var, 2),
            "gradient_variance": round(grad_var, 2),
            "noise_dispersion": round(noise_dispersion, 3),
            "blocking_ratio": round(blocking_ratio, 3),
            "signals": signals,
            "latency_ms": latency_ms
        }

    def _load_image(self, media_input: Any) -> Optional[np.ndarray]:
        """Loads media input into an RGB/BGR numpy array."""
        if media_input is None:
            return None
        if isinstance(media_input, np.ndarray):
            return media_input
        if isinstance(media_input, (str, Path)):
            p = Path(media_input)
            if p.exists() and p.is_file():
                img = cv2.imread(str(p))
                if img is None:
                    # Video fallback frame extract
                    cap = cv2.VideoCapture(str(p))
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            img = frame
                        cap.release()
                return img
        if isinstance(media_input, bytes):
            nparr = np.frombuffer(media_input, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return None


# Global singleton instance
global_visual_forensics = GlobalVisualForensics()
