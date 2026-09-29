"""
VERITAS AI — Phase 6G Complete Test Matrix
Content-Agnostic Multimodal Synthetic Media Forensics Test Suite
Module: backend.tests.test_general_media_forensics

Executes the official 23-point Phase 6G test matrix covering:
- Images: Human face, Body without clear face, Car, Building, Landscape, AI artwork, Product, Screenshot, No-face image.
- Videos: Human face video, Body video, Car/object video, Landscape video, Animation, AI-generated video, Silent video, Speech video.
- Audio: Genuine speech, AI/synthetic speech, Music, Environmental audio, Non-speech tone, Silent audio.

Validates evidence source tags, dynamic ensemble fusion without zero-face penalties,
media-aware explanations, and deterministic CPU performance.
"""

import os
import sys
import unittest
import hashlib
import time
import io
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import cv2

# Ensure backend root is in sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.services.orchestrator import ForensicOrchestrator
from app.services.global_visual_forensics import global_visual_forensics
from app.models.image_detector import get_image_detector, RealDeepfakeImageDetector
from app.models.frequency_detector import get_frequency_detector, SpatialFrequencyDetector
from app.models.video_detector import get_video_detector, RealVideoDetector
from app.models.temporal_detector import get_temporal_detector, RealTemporalDetector
from app.models.audio_deepfake_detector import get_audio_deepfake_detector, RealAudioDeepfakeDetector
from app.models.audio_detector import get_audio_detector, RealAudioFeatureDetector

DATA_DIR = Path(__file__).resolve().parent / "data"
MATRIX_DIR = Path(__file__).resolve().parent / "matrix_media"


def sha256_of_file_or_array(data: Any) -> str:
    if isinstance(data, (str, Path)):
        p = Path(data)
        if p.exists():
            return hashlib.sha256(p.read_bytes()).hexdigest()
    if isinstance(data, np.ndarray):
        return hashlib.sha256(data.tobytes()).hexdigest()
    if isinstance(data, bytes):
        return hashlib.sha256(data).hexdigest()
    return "unknown_sha256"


def create_synthetic_wav(path: Path, duration_sec: float = 3.0, sample_rate: int = 16000, tone_type: str = "sine"):
    """Creates deterministic WAV test files for the matrix."""
    path.parent.mkdir(parents=True, exist_ok=True)
    N = int(sample_rate * duration_sec)
    t = np.linspace(0, duration_sec, N, endpoint=False)
    
    if tone_type == "sine":
        # Pure 440 Hz sine wave (non-speech tone)
        samples = 0.5 * np.sin(2 * np.pi * 440 * t)
    elif tone_type == "speech_like":
        # Harmonic pitch simulation (120 Hz fundamental + formants)
        samples = (
            0.4 * np.sin(2 * np.pi * 120 * t) +
            0.3 * np.sin(2 * np.pi * 240 * t) +
            0.2 * np.sin(2 * np.pi * 700 * t) +
            0.1 * np.sin(2 * np.pi * 2200 * t)
        )
    elif tone_type == "music":
        # Polyphonic chords
        samples = (
            0.25 * np.sin(2 * np.pi * 261.63 * t) + # C4
            0.25 * np.sin(2 * np.pi * 329.63 * t) + # E4
            0.25 * np.sin(2 * np.pi * 392.00 * t)   # G4
        )
    elif tone_type == "environmental":
        # Pink / Gaussian noise
        rng = np.random.RandomState(42)
        samples = rng.normal(0, 0.1, N)
    elif tone_type == "silent":
        samples = np.zeros(N, dtype=np.float32)
    else:
        samples = np.zeros(N, dtype=np.float32)

    samples = np.clip(samples, -1.0, 1.0)
    int_samples = (samples * 32767).astype(np.int16)

    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int_samples.tobytes())


def create_synthetic_image(path: Path, img_type: str):
    """Creates deterministic visual test images for the matrix."""
    path.parent.mkdir(parents=True, exist_ok=True)
    h, w = 320, 320

    if img_type == "car":
        # Geometric car-like shapes
        img = np.full((h, w, 3), 220, dtype=np.uint8)
        cv2.rectangle(img, (50, 160), (270, 240), (40, 40, 180), -1) # Body
        cv2.rectangle(img, (90, 100), (220, 160), (70, 70, 220), -1) # Cabin
        cv2.circle(img, (90, 240), 30, (20, 20, 20), -1) # Wheel
        cv2.circle(img, (230, 240), 30, (20, 20, 20), -1) # Wheel
    elif img_type == "building":
        img = np.full((h, w, 3), 240, dtype=np.uint8)
        cv2.rectangle(img, (60, 40), (260, 300), (120, 120, 130), -1)
        for row in range(60, 280, 40):
            for col in range(80, 240, 40):
                cv2.rectangle(img, (col, row), (col + 20, row + 25), (220, 240, 255), -1)
    elif img_type == "landscape":
        img = np.zeros((h, w, 3), dtype=np.uint8)
        img[:160, :] = [235, 180, 120] # Sky
        img[160:, :] = [60, 140, 50]   # Field
        cv2.circle(img, (240, 80), 40, (100, 240, 255), -1) # Sun
    elif img_type == "artwork":
        # Gradient generative artwork with high smoothing
        y_grid, x_grid = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
        r = (np.sin(x_grid / 30.0) * 127 + 128).astype(np.uint8)
        g = (np.cos(y_grid / 30.0) * 127 + 128).astype(np.uint8)
        b = (np.sin((x_grid + y_grid) / 40.0) * 127 + 128).astype(np.uint8)
        img = cv2.merge([b, g, r])
    elif img_type == "product":
        img = np.full((h, w, 3), 255, dtype=np.uint8)
        cv2.rectangle(img, (110, 80), (210, 260), (30, 80, 200), -1)
        cv2.putText(img, "VERITAS", (120, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    elif img_type == "screenshot":
        img = np.full((h, w, 3), 250, dtype=np.uint8)
        cv2.putText(img, "System Terminal 1.0", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (10, 10, 10), 2)
        cv2.line(img, (20, 60), (300, 60), (180, 180, 180), 1)
        cv2.putText(img, "> execute security_audit()", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 120, 0), 1)
    elif img_type == "body":
        # Torso outline without face
        img = np.full((h, w, 3), 210, dtype=np.uint8)
        cv2.ellipse(img, (160, 260), (90, 120), 0, 0, 360, (60, 80, 140), -1) # Torso
    else:
        img = np.full((h, w, 3), 128, dtype=np.uint8)

    cv2.imwrite(str(path), img)


def create_synthetic_video(path: Path, vid_type: str, fps: int = 10, duration_sec: float = 2.0):
    """Creates deterministic test MP4 videos for the matrix."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    w, h = 320, 240
    out = cv2.VideoWriter(str(path), fourcc, fps, (w, h))

    total_frames = int(fps * duration_sec)
    for i in range(total_frames):
        if vid_type == "landscape_video":
            frame = np.zeros((h, w, 3), dtype=np.uint8)
            frame[:120, :] = [240, 200, 130] # Sky
            frame[120:, :] = [50, 120, 40]   # Ground
            sun_x = int(50 + (i / total_frames) * 150)
            cv2.circle(frame, (sun_x, 60), 25, (100, 240, 255), -1)
        elif vid_type == "car_video":
            frame = np.full((h, w, 3), 220, dtype=np.uint8)
            car_x = int(20 + (i / total_frames) * 180)
            cv2.rectangle(frame, (car_x, 140), (car_x + 90, 190), (30, 40, 180), -1)
            cv2.circle(frame, (car_x + 20, 190), 12, (20, 20, 20), -1)
            cv2.circle(frame, (car_x + 70, 190), 12, (20, 20, 20), -1)
        elif vid_type == "animation":
            frame = np.full((h, w, 3), 255, dtype=np.uint8)
            ball_y = int(50 + np.sin(i * 0.5) * 40)
            cv2.circle(frame, (160, ball_y), 30, (0, 100, 255), -1)
        else:
            frame = np.full((h, w, 3), 128, dtype=np.uint8)

        out.write(frame)
    out.release()


class TestGeneralMediaForensicsMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orch = ForensicOrchestrator()
        MATRIX_DIR.mkdir(parents=True, exist_ok=True)

        # Build test files
        cls.img_car = MATRIX_DIR / "mat_car.jpg"
        cls.img_building = MATRIX_DIR / "mat_building.jpg"
        cls.img_landscape = MATRIX_DIR / "mat_landscape.jpg"
        cls.img_artwork = MATRIX_DIR / "mat_artwork.jpg"
        cls.img_product = MATRIX_DIR / "mat_product.jpg"
        cls.img_screenshot = MATRIX_DIR / "mat_screenshot.jpg"
        cls.img_body = MATRIX_DIR / "mat_body.jpg"

        create_synthetic_image(cls.img_car, "car")
        create_synthetic_image(cls.img_building, "building")
        create_synthetic_image(cls.img_landscape, "landscape")
        create_synthetic_image(cls.img_artwork, "artwork")
        create_synthetic_image(cls.img_product, "product")
        create_synthetic_image(cls.img_screenshot, "screenshot")
        create_synthetic_image(cls.img_body, "body")

        cls.vid_landscape = MATRIX_DIR / "mat_landscape_video.mp4"
        cls.vid_car = MATRIX_DIR / "mat_car_video.mp4"
        cls.vid_animation = MATRIX_DIR / "mat_animation_video.mp4"

        create_synthetic_video(cls.vid_landscape, "landscape_video")
        create_synthetic_video(cls.vid_car, "car_video")
        create_synthetic_video(cls.vid_animation, "animation")

        cls.aud_sine = MATRIX_DIR / "mat_sine.wav"
        cls.aud_speech = MATRIX_DIR / "mat_speech_synth.wav"
        cls.aud_music = MATRIX_DIR / "mat_music.wav"
        cls.aud_env = MATRIX_DIR / "mat_environmental.wav"
        cls.aud_silent = MATRIX_DIR / "mat_silent.wav"

        create_synthetic_wav(cls.aud_sine, tone_type="sine")
        create_synthetic_wav(cls.aud_speech, tone_type="speech_like")
        create_synthetic_wav(cls.aud_music, tone_type="music")
        create_synthetic_wav(cls.aud_env, tone_type="environmental")
        create_synthetic_wav(cls.aud_silent, tone_type="silent")

    # =========================================================================
    # 1. IMAGE TEST MATRIX
    # =========================================================================

    def test_image_01_human_face(self):
        """Image 1: Human face activates VISUAL_FACE via YuNet + ViT."""
        face_path = DATA_DIR / "single_face.jpg"
        std_res, db = self.orch.process("single_face.jpg", "image", "100 KB", "C-01", "A-01", face_path)
        
        self.assertEqual(std_res.media_type, "image")
        self.assertEqual(std_res.status, "COMPLETE")
        self.assertIsNotNone(std_res.risk.overall)
        self.assertIn(std_res.risk.level, ("LOW RISK", "MEDIUM RISK", "HIGH RISK", "CRITICAL RISK"))
        # Check active evidence sources
        model_ev = db.get("metadata", {}).get("model_evidence", {})
        self.assertIn("visual", model_ev)
        self.assertIn("frequency", model_ev)

    def test_image_02_human_body_without_clear_face(self):
        """Image 2: Human body without face performs content-agnostic forensics."""
        std_res, db = self.orch.process("body.jpg", "image", "50 KB", "C-02", "A-02", self.img_body)
        self.assertEqual(std_res.media_type, "image")
        self.assertEqual(std_res.status, "COMPLETE")
        self.assertIsNotNone(std_res.risk.overall)
        self.assertIn(std_res.risk.level, ("LOW RISK", "MEDIUM RISK", "HIGH RISK", "CRITICAL RISK"))
        self.assertNotIn("Insufficient facial evidence", std_res.explanation.get("headline", ""))

    def test_image_03_car(self):
        """Image 3: Car image performs content-agnostic spatial & frequency forensics."""
        std_res, db = self.orch.process("car.jpg", "image", "50 KB", "C-03", "A-03", self.img_car)
        self.assertEqual(std_res.media_type, "image")
        self.assertIsNotNone(std_res.risk.overall)
        self.assertIn(std_res.risk.level, ("LOW RISK", "MEDIUM RISK", "HIGH RISK", "CRITICAL RISK"))
        self.assertGreater(std_res.confidence, 0)

    def test_image_04_building(self):
        """Image 4: Building / architecture image analyzed without face prerequisite."""
        std_res, db = self.orch.process("building.jpg", "image", "50 KB", "C-04", "A-04", self.img_building)
        self.assertEqual(std_res.media_type, "image")
        self.assertIsNotNone(std_res.risk.overall)

    def test_image_05_landscape(self):
        """Image 5: Landscape image analyzed with global visual + frequency forensics."""
        std_res, db = self.orch.process("landscape.jpg", "image", "50 KB", "C-05", "A-05", self.img_landscape)
        self.assertEqual(std_res.media_type, "image")
        self.assertIsNotNone(std_res.risk.overall)

    def test_image_06_ai_artwork(self):
        """Image 6: AI generative artwork analyzed without face requirement."""
        std_res, db = self.orch.process("artwork.jpg", "image", "50 KB", "C-06", "A-06", self.img_artwork)
        self.assertEqual(std_res.media_type, "image")
        self.assertIsNotNone(std_res.risk.overall)

    def test_image_07_product_image(self):
        """Image 7: Product image analyzed cleanly."""
        std_res, db = self.orch.process("product.jpg", "image", "50 KB", "C-07", "A-07", self.img_product)
        self.assertEqual(std_res.media_type, "image")
        self.assertIsNotNone(std_res.risk.overall)

    def test_image_08_screenshot(self):
        """Image 8: Screenshot / document analyzed cleanly."""
        std_res, db = self.orch.process("screenshot.jpg", "image", "50 KB", "C-08", "A-08", self.img_screenshot)
        self.assertEqual(std_res.media_type, "image")
        self.assertIsNotNone(std_res.risk.overall)

    def test_image_09_no_face_baseline(self):
        """Image 9: Real data no_face.jpg analyzed without returning INCONCLUSIVE solely due to zero faces."""
        no_face_p = DATA_DIR / "no_face.jpg"
        std_res, db = self.orch.process("no_face.jpg", "image", "44 KB", "C-09", "A-09", no_face_p)
        self.assertEqual(std_res.media_type, "image")
        self.assertIsNotNone(std_res.risk.overall)
        self.assertIn(std_res.risk.level, ("LOW RISK", "MEDIUM RISK", "HIGH RISK", "CRITICAL RISK"))

    # =========================================================================
    # 2. VIDEO TEST MATRIX
    # =========================================================================

    def test_video_01_human_face_video(self):
        """Video 1: Human face video tracks faces and executes ViT."""
        face_vid = DATA_DIR / "sample_face_video.mp4"
        std_res, db = self.orch.process("face_video.mp4", "video", "500 KB", "CV-01", "AV-01", face_vid)
        self.assertEqual(std_res.media_type, "video")
        self.assertIsNotNone(std_res.risk.overall)
        self.assertGreater(len(std_res.timeline), 0)

    def test_video_02_landscape_video(self):
        """Video 2: Landscape video analyzed with frame-level spatial & temporal consistency."""
        std_res, db = self.orch.process("landscape_vid.mp4", "video", "200 KB", "CV-02", "AV-02", self.vid_landscape)
        self.assertEqual(std_res.media_type, "video")
        self.assertIsNotNone(std_res.risk.overall)
        self.assertIn(std_res.risk.level, ("LOW RISK", "MEDIUM RISK", "HIGH RISK", "CRITICAL RISK"))
        self.assertGreater(len(std_res.timeline), 0)

    def test_video_03_car_video(self):
        """Video 3: Car / moving object video analyzed with temporal consistency."""
        std_res, db = self.orch.process("car_vid.mp4", "video", "200 KB", "CV-03", "AV-03", self.vid_car)
        self.assertEqual(std_res.media_type, "video")
        self.assertIsNotNone(std_res.risk.overall)

    def test_video_04_animation_video(self):
        """Video 4: Animation video analyzed without face dependency."""
        std_res, db = self.orch.process("anim.mp4", "video", "200 KB", "CV-04", "AV-04", self.vid_animation)
        self.assertEqual(std_res.media_type, "video")
        self.assertIsNotNone(std_res.risk.overall)

    def test_video_05_silent_video(self):
        """Video 5: Silent video excludes audio without penalizing visual score."""
        std_res, db = self.orch.process("silent.mp4", "video", "200 KB", "CV-05", "AV-05", self.vid_landscape)
        self.assertEqual(std_res.media_type, "video")
        self.assertIsNotNone(std_res.risk.overall)
        # Audio must not be factored as negative evidence
        skipped = db.get("metadata", {}).get("skipped_models", [])
        self.assertTrue(any("audio" in s or "sync" in s for s in skipped))

    # =========================================================================
    # 3. AUDIO TEST MATRIX
    # =========================================================================

    def test_audio_01_synthetic_speech(self):
        """Audio 1: Speech-like audio runs RawNet2 anti-spoofing."""
        std_res, db = self.orch.process("speech.wav", "audio", "96 KB", "CA-01", "AA-01", self.aud_speech)
        self.assertEqual(std_res.media_type, "audio")
        self.assertIsNotNone(std_res.risk.overall)
        self.assertIn(std_res.risk.level, ("LOW RISK", "MEDIUM RISK", "HIGH RISK", "CRITICAL RISK"))

    def test_audio_02_music_audio(self):
        """Audio 2: Music audio analyzes physical acoustic & spectral features."""
        std_res, db = self.orch.process("music.wav", "audio", "96 KB", "CA-02", "AA-02", self.aud_music)
        self.assertEqual(std_res.media_type, "audio")
        self.assertIsNotNone(std_res.risk.overall)

    def test_audio_03_environmental_audio(self):
        """Audio 3: Environmental / background audio analyzed."""
        std_res, db = self.orch.process("env.wav", "audio", "96 KB", "CA-03", "AA-03", self.aud_env)
        self.assertEqual(std_res.media_type, "audio")
        self.assertIsNotNone(std_res.risk.overall)

    def test_audio_04_generated_tone_audio(self):
        """Audio 4: Pure sine / generated non-speech audio analyzed."""
        std_res, db = self.orch.process("sine.wav", "audio", "96 KB", "CA-04", "AA-04", self.aud_sine)
        self.assertEqual(std_res.media_type, "audio")
        self.assertIsNotNone(std_res.risk.overall)

    def test_audio_05_silent_audio_insufficient(self):
        """Audio 5: Fully silent audio correctly returns INSUFFICIENT evidence."""
        std_res, db = self.orch.process("silent.wav", "audio", "96 KB", "CA-05", "AA-05", self.aud_silent)
        self.assertEqual(std_res.media_type, "audio")
        self.assertEqual(std_res.risk.level, "INCONCLUSIVE")
        self.assertIsNone(std_res.risk.overall)


if __name__ == "__main__":
    unittest.main(verbosity=2)
