"""
VERITAS AI — Forensic Face Detection Adapter Architecture
Module: backend.app.models.face_detector

Implements lightweight, high-performance face detection for CPU execution
utilizing the official OpenCV YuNet ONNX model (Apache-2.0 / MIT license).
Extracts real bounding boxes, continuous confidence scores (0.0-1.0),
5-point facial landmarks, normalized crops, and multi-frame face tracking.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import os
import math
import logging
import urllib.request
import numpy as np
import cv2

logger = logging.getLogger("veritas.forensics.face_detector")

# Official OpenCV Model Zoo release for YuNet face detector
YUNET_OFFICIAL_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "face_detection_yunet/face_detection_yunet_2023mar.onnx"
)

DEFAULT_WEIGHTS_DIR = Path(__file__).resolve().parent.parent / "weights"
DEFAULT_YUNET_PATH = DEFAULT_WEIGHTS_DIR / "face_detection_yunet_2023mar.onnx"


# =============================================================================
# 1. DetectedFace Data Structure
# =============================================================================

@dataclass
class DetectedFace:
    """
    Forensic representation of a detected facial region of interest.
    All coordinate values, landmarks, and confidence metrics are real model outputs.
    """
    x: int
    y: int
    width: int
    height: int
    confidence: float
    frame_number: int = 1
    timestamp_sec: float = 0.0
    crop_tensor_shape: Tuple[int, int, int] = (3, 224, 224)
    landmarks: Optional[List[Tuple[float, float]]] = None
    face_crop: Optional[np.ndarray] = field(default=None, repr=False)
    tracking_id: Optional[int] = None
    is_mock: bool = False
    detection_mode: str = "REAL_AI_YUNET"

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Returns standard (x, y, width, height) tuple."""
        return (self.x, self.y, self.width, self.height)

    @property
    def landmarks_ready(self) -> bool:
        """Indicates if 5-point facial landmarks are populated."""
        return bool(self.landmarks and len(self.landmarks) >= 5)

    def to_dict(self, include_crop_meta: bool = True) -> Dict[str, Any]:
        """JSON-safe dictionary representation for API serialization."""
        data: Dict[str, Any] = {
            "bbox": self.bbox,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": round(float(self.confidence), 4),
            "frame_number": self.frame_number,
            "timestamp_sec": round(float(self.timestamp_sec), 2),
            "crop_tensor_shape": list(self.crop_tensor_shape),
            "landmarks_ready": self.landmarks_ready,
            "landmarks": self.landmarks,
            "tracking_id": self.tracking_id,
            "is_mock": self.is_mock,
            "detection_mode": self.detection_mode,
        }
        if include_crop_meta and self.face_crop is not None:
            data["crop_shape"] = list(self.face_crop.shape)
        return data


# =============================================================================
# 2. Abstract Base Detector Interface
# =============================================================================

class FaceDetector(ABC):
    """Abstract base detector interface for facial region-of-interest extraction."""

    @abstractmethod
    def detect_faces(
        self,
        image_np: np.ndarray,
        frame_number: int = 1,
        timestamp_sec: float = 0.0
    ) -> List[DetectedFace]:
        """
        Detect faces in a single RGB image array.
        Returns a list of DetectedFace objects with real bounding boxes and confidences.
        """
        pass


# =============================================================================
# 3. Real Face Detector (OpenCV YuNet ONNX)
# =============================================================================

class RealFaceDetector(FaceDetector):
    """
    Production Real Face Detector utilizing OpenCV YuNet DNN.
    - Model: YuNet (Shiqi Yu / OpenCV Zoo)
    - Weight file size: ~232 KB
    - License: Apache 2.0 / MIT
    - CPU Optimized: Sub-15ms inference latency on modern Intel CPUs.
    - Continuous real confidence scores (0.0 to 1.0).
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        score_threshold: float = 0.40,
        nms_threshold: float = 0.3,
        max_faces: int = 10,
        max_input_dim: int = 1280,
        crop_size: Tuple[int, int] = (224, 224)
    ):
        self.model_path = Path(model_path) if model_path else DEFAULT_YUNET_PATH
        self.score_threshold = score_threshold
        self.nms_threshold = nms_threshold
        self.max_faces = max_faces
        self.max_input_dim = max_input_dim
        self.crop_size = crop_size
        self._ensure_weights()
        self._init_detector()

    def _ensure_weights(self) -> None:
        """Ensures the lightweight ONNX weights exist locally or downloads them."""
        if not self.model_path.exists():
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info("Downloading official OpenCV YuNet model (~232KB) to %s...", self.model_path)
            try:
                urllib.request.urlretrieve(YUNET_OFFICIAL_URL, str(self.model_path))
                logger.info("YuNet model weights successfully downloaded.")
            except Exception as e:
                logger.error("Failed to download YuNet weights: %s", e)
                raise RuntimeError(
                    f"Face detector model weights missing at {self.model_path} and download failed: {e}"
                )

    def _init_detector(self) -> None:
        """Initializes the cv2.FaceDetectorYN instance with CPU target."""
        try:
            self.detector = cv2.FaceDetectorYN.create(
                model=str(self.model_path),
                config="",
                input_size=(320, 320),
                score_threshold=self.score_threshold,
                nms_threshold=self.nms_threshold,
                top_k=5000,
                backend_id=cv2.dnn.DNN_BACKEND_OPENCV,
                target_id=cv2.dnn.DNN_TARGET_CPU
            )
        except Exception as e:
            logger.error("Failed to initialize cv2.FaceDetectorYN: %s", e)
            raise

    def detect_faces(
        self,
        image_np: np.ndarray,
        frame_number: int = 1,
        timestamp_sec: float = 0.0
    ) -> List[DetectedFace]:
        """
        Executes real face detection on an RGB image array.
        Handles grayscale/RGBA conversions, scale optimization, and bounding box validation.
        """
        if image_np is None or not isinstance(image_np, np.ndarray) or image_np.size == 0:
            return []

        # Standardize channels to 3-channel RGB
        if len(image_np.shape) == 2:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
        elif len(image_np.shape) == 3 and image_np.shape[2] == 4:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2RGB)
        elif len(image_np.shape) != 3 or image_np.shape[2] != 3:
            return []

        h, w = image_np.shape[:2]
        if h < 10 or w < 10:
            return []

        # OpenCV YuNet requires BGR input
        bgr_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

        # CPU optimization: Downscale input if exceeding max_input_dim
        scale = 1.0
        if max(h, w) > self.max_input_dim:
            scale = self.max_input_dim / float(max(h, w))
            det_w = int(w * scale)
            det_h = int(h * scale)
            proc_img = cv2.resize(bgr_image, (det_w, det_h), interpolation=cv2.INTER_AREA)
        else:
            det_w, det_h = w, h
            proc_img = bgr_image

        # Update input size and run inference
        self.detector.setInputSize((det_w, det_h))
        _, raw_faces = self.detector.detect(proc_img)

        if raw_faces is None or len(raw_faces) == 0:
            return []

        detected: List[DetectedFace] = []
        for i, face_data in enumerate(raw_faces):
            if i >= self.max_faces:
                break

            # Rescale coordinates to original image space
            fx = float(face_data[0]) / scale
            fy = float(face_data[1]) / scale
            fw = float(face_data[2]) / scale
            fh = float(face_data[3]) / scale
            conf = float(face_data[14])

            # Clamp bounding box inside image boundaries
            x1 = max(0, min(int(fx), w - 1))
            y1 = max(0, min(int(fy), h - 1))
            box_w = max(1, min(int(fw), w - x1))
            box_h = max(1, min(int(fh), h - y1))

            # Extract 5 facial landmarks (right eye, left eye, nose tip, right mouth, left mouth)
            landmarks: List[Tuple[float, float]] = []
            for lm_idx in range(5):
                lm_x = float(face_data[4 + lm_idx * 2]) / scale
                lm_y = float(face_data[5 + lm_idx * 2]) / scale
                landmarks.append((round(lm_x, 1), round(lm_y, 1)))

            # Extract normalized face crop with 10% context margin
            pad_x = int(box_w * 0.1)
            pad_y = int(box_h * 0.1)
            crop_x1 = max(0, x1 - pad_x)
            crop_y1 = max(0, y1 - pad_y)
            crop_x2 = min(w, x1 + box_w + pad_x)
            crop_y2 = min(h, y1 + box_h + pad_y)

            crop_arr = image_np[crop_y1:crop_y2, crop_x1:crop_x2]
            if crop_arr.size > 0:
                resized_crop = cv2.resize(crop_arr, self.crop_size, interpolation=cv2.INTER_LINEAR)
            else:
                resized_crop = np.zeros((*self.crop_size, 3), dtype=np.uint8)

            detected.append(DetectedFace(
                x=x1,
                y=y1,
                width=box_w,
                height=box_h,
                confidence=conf,
                frame_number=frame_number,
                timestamp_sec=timestamp_sec,
                crop_tensor_shape=(3, self.crop_size[0], self.crop_size[1]),
                landmarks=landmarks,
                face_crop=resized_crop,
                is_mock=False,
                detection_mode="REAL_AI_YUNET"
            ))

        return detected


# =============================================================================
# 4. Mock Face Detector (Heuristic Fallback)
# =============================================================================

class MockFaceDetector(FaceDetector):
    """
    Simulated detector fallback for offline/demo tests.
    Explicitly tagged as DEMO MODE // SIMULATED FACE DETECTION.
    """

    def detect_faces(
        self,
        image_np: np.ndarray,
        frame_number: int = 1,
        timestamp_sec: float = 0.0
    ) -> List[DetectedFace]:
        if image_np is None or image_np.size == 0:
            return []

        h, w = image_np.shape[:2]
        box_w = int(w * 0.35)
        box_h = int(h * 0.40)
        box_x = max(0, min(int((w - box_w) / 2), w - box_w))
        box_y = max(0, min(int(h * 0.18), h - box_h))

        crop_arr = image_np[box_y:box_y + box_h, box_x:box_x + box_w]
        resized_crop = (
            cv2.resize(crop_arr, (224, 224))
            if crop_arr.size > 0
            else np.zeros((224, 224, 3), dtype=np.uint8)
        )

        return [
            DetectedFace(
                x=box_x,
                y=box_y,
                width=box_w,
                height=box_h,
                confidence=0.50,
                frame_number=frame_number,
                timestamp_sec=timestamp_sec,
                crop_tensor_shape=(3, 224, 224),
                landmarks=None,
                face_crop=resized_crop,
                is_mock=True,
                detection_mode="DEMO MODE // SIMULATED FACE DETECTION"
            )
        ]


# =============================================================================
# 5. Temporal Video Face Tracker Helper
# =============================================================================

class SimpleFaceTracker:
    """
    Lightweight greedy centroid/IoU multi-frame face tracker.
    Assigns stable integer tracking IDs across consecutive sampled video frames.
    """

    def __init__(self, max_distance_pixels: float = 100.0):
        self.max_distance_pixels = max_distance_pixels
        self.next_track_id = 0
        self.active_tracks: Dict[int, Tuple[float, float]] = {}  # track_id -> (center_x, center_y)

    def track(self, faces: List[DetectedFace]) -> List[DetectedFace]:
        """Assigns tracking IDs to faces detected in the current frame."""
        if not faces:
            return faces

        updated_tracks: Dict[int, Tuple[float, float]] = {}
        unmatched_faces = list(faces)

        # Match existing tracks to nearest face in current frame
        for track_id, (prev_cx, prev_cy) in list(self.active_tracks.items()):
            best_face = None
            best_dist = float("inf")
            for face in unmatched_faces:
                cx = face.x + face.width / 2.0
                cy = face.y + face.height / 2.0
                dist = math.hypot(cx - prev_cx, cy - prev_cy)
                if dist < best_dist and dist <= self.max_distance_pixels:
                    best_dist = dist
                    best_face = face

            if best_face is not None:
                best_face.tracking_id = track_id
                cx = best_face.x + best_face.width / 2.0
                cy = best_face.y + best_face.height / 2.0
                updated_tracks[track_id] = (cx, cy)
                unmatched_faces.remove(best_face)

        # Assign new track IDs for newly appeared faces
        for new_face in unmatched_faces:
            new_id = self.next_track_id
            self.next_track_id += 1
            new_face.tracking_id = new_id
            cx = new_face.x + new_face.width / 2.0
            cy = new_face.y + new_face.height / 2.0
            updated_tracks[new_id] = (cx, cy)

        self.active_tracks = updated_tracks
        return faces


# =============================================================================
# 6. Global Factory
# =============================================================================

def get_face_detector(force_mock: bool = False) -> FaceDetector:
    """Factory creating the primary real face detector or mock fallback."""
    if force_mock:
        return MockFaceDetector()
    try:
        return RealFaceDetector()
    except Exception as e:
        logger.warning(
            "RealFaceDetector unavailable (%s). Falling back to MockFaceDetector (DEMO MODE).", e
        )
        return MockFaceDetector()
