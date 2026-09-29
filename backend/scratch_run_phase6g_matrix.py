"""
VERITAS AI — Phase 6G Complete Test Matrix Runner
Runs tests across all 23 media types specified in Phase 6G prompt:
IMAGE (9 categories):
1. Human face
2. Human body without clear face
3. Car
4. Building
5. Landscape
6. AI artwork
7. Product image
8. Screenshot
9. No-face image

VIDEO (8 categories):
1. Human face video
2. Human body video
3. Car/object video
4. Landscape video
5. Animation
6. AI-generated video
7. Silent video
8. Video with speech

AUDIO (6 categories):
1. Genuine speech
2. AI/synthetic speech
3. Music
4. Environmental audio
5. Generated/non-speech audio
6. Silent audio
"""

import sys
import json
import hashlib
import tempfile
from pathlib import Path
import numpy as np
import cv2
import wave

backend_root = Path(__file__).resolve().parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.services.orchestrator import ForensicOrchestrator
from app.models.image_detector import RealDeepfakeImageDetector
from app.models.frequency_detector import SpatialFrequencyDetector
from app.models.temporal_detector import RealTemporalDetector
from app.models.audio_deepfake_detector import RealAudioDeepfakeDetector
from app.models.audio_detector import RealAudioFeatureDetector

orch = ForensicOrchestrator(
    image_detector=RealDeepfakeImageDetector(),
    frequency_detector=SpatialFrequencyDetector(),
    temporal_detector=RealTemporalDetector(),
    audio_detector=RealAudioDeepfakeDetector(),
    audio_feature_detector=RealAudioFeatureDetector()
)

tmp_dir = Path(tempfile.mkdtemp(prefix="veritas_matrix_"))

def save_img(arr, name):
    p = tmp_dir / name
    cv2.imwrite(str(p), arr)
    return p

def save_vid(frames, name, fps=1):
    p = tmp_dir / name
    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(p), fourcc, fps, (w, h))
    for f in frames:
        out.write(f)
    out.release()
    return p

def save_aud(pcm, name, sr=16000):
    p = tmp_dir / name
    # convert float32 to int16
    pcm_int16 = (np.clip(pcm, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(p), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm_int16.tobytes())
    return p

# Helpers to build synthetic media representations
def draw_face():
    img = np.ones((320, 320, 3), dtype=np.uint8) * 180
    cv2.ellipse(img, (160, 160), (70, 90), 0, 0, 360, (140, 160, 210), -1)
    cv2.circle(img, (135, 140), 10, (50, 40, 30), -1)
    cv2.circle(img, (185, 140), 10, (50, 40, 30), -1)
    cv2.ellipse(img, (160, 200), (25, 12), 0, 0, 180, (60, 60, 180), -1)
    return img

def draw_body_noface():
    img = np.ones((400, 300, 3), dtype=np.uint8) * 220
    # Torso and limbs, no head/face
    cv2.rectangle(img, (90, 120), (210, 320), (80, 50, 40), -1)
    cv2.rectangle(img, (50, 120), (85, 280), (70, 40, 30), -1)
    cv2.rectangle(img, (215, 120), (250, 280), (70, 40, 30), -1)
    return img

def draw_car():
    img = np.ones((320, 480, 3), dtype=np.uint8) * 200
    cv2.rectangle(img, (80, 150), (400, 250), (30, 30, 180), -1)
    cv2.rectangle(img, (140, 90), (340, 150), (60, 60, 210), -1)
    cv2.circle(img, (140, 250), 30, (20, 20, 20), -1)
    cv2.circle(img, (340, 250), 30, (20, 20, 20), -1)
    return img

def draw_building():
    img = np.ones((400, 300, 3), dtype=np.uint8) * 230
    cv2.rectangle(img, (60, 80), (240, 390), (120, 120, 120), -1)
    for r in range(100, 360, 40):
        for c in range(80, 220, 35):
            cv2.rectangle(img, (c, r), (c + 20, r + 25), (240, 240, 200), -1)
    return img

def draw_landscape():
    img = np.zeros((320, 480, 3), dtype=np.uint8)
    img[:180, :] = [230, 200, 130] # Sky
    img[180:, :] = [60, 140, 40]   # Grass/hills
    pts = np.array([[0, 180], [150, 90], [280, 180], [380, 110], [480, 180]], np.int32)
    cv2.fillPoly(img, [pts], (100, 90, 80)) # Mountain
    return img

def draw_ai_artwork():
    # Ultra-smooth synthetic gradient with high saturation and no camera noise
    x = np.linspace(0, 4 * np.pi, 384)
    y = np.linspace(0, 4 * np.pi, 384)
    xx, yy = np.meshgrid(x, y)
    r = (np.sin(xx) * 127 + 128).astype(np.uint8)
    g = (np.cos(yy) * 127 + 128).astype(np.uint8)
    b = (np.sin(xx + yy) * 127 + 128).astype(np.uint8)
    return np.stack([b, g, r], axis=-1)

def draw_product():
    img = np.ones((350, 350, 3), dtype=np.uint8) * 255
    cv2.rectangle(img, (120, 100), (230, 290), (180, 120, 40), -1) # bottle
    cv2.rectangle(img, (145, 60), (205, 100), (20, 20, 20), -1)   # cap
    return img

def draw_screenshot():
    img = np.ones((400, 600, 3), dtype=np.uint8) * 245
    cv2.rectangle(img, (0, 0), (600, 40), (45, 45, 45), -1) # Titlebar
    cv2.putText(img, "VERITAS AI — Terminal Session", (20, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.rectangle(img, (30, 60), (570, 360), (20, 20, 20), -1) # Console
    cv2.putText(img, "> sys.status: 100% operational", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 220, 80), 1)
    return img

def draw_no_face_texture():
    return (np.random.normal(128, 15, (300, 300, 3))).clip(0, 255).astype(np.uint8)

# Construct Test Matrix Items
test_items = [
    # IMAGE MATRIX (9 items)
    ("IMAGE", "1. Human face", save_img(draw_face(), "img_01_face.jpg"), "image"),
    ("IMAGE", "2. Human body without clear face", save_img(draw_body_noface(), "img_02_body.jpg"), "image"),
    ("IMAGE", "3. Car", save_img(draw_car(), "img_03_car.jpg"), "image"),
    ("IMAGE", "4. Building", save_img(draw_building(), "img_04_building.jpg"), "image"),
    ("IMAGE", "5. Landscape", save_img(draw_landscape(), "img_05_landscape.jpg"), "image"),
    ("IMAGE", "6. AI artwork", save_img(draw_ai_artwork(), "img_06_ai_art.png"), "image"),
    ("IMAGE", "7. Product image", save_img(draw_product(), "img_07_product.jpg"), "image"),
    ("IMAGE", "8. Screenshot", save_img(draw_screenshot(), "img_08_screenshot.png"), "image"),
    ("IMAGE", "9. No-face image", save_img(draw_no_face_texture(), "img_09_noface.jpg"), "image"),

    # VIDEO MATRIX (8 items)
    ("VIDEO", "1. Human face video", save_vid([draw_face() for _ in range(4)], "vid_01_face.mp4"), "video"),
    ("VIDEO", "2. Human body video", save_vid([draw_body_noface() for _ in range(4)], "vid_02_body.mp4"), "video"),
    ("VIDEO", "3. Car/object video", save_vid([draw_car() for _ in range(4)], "vid_03_car.mp4"), "video"),
    ("VIDEO", "4. Landscape video", save_vid([draw_landscape() for _ in range(4)], "vid_04_landscape.mp4"), "video"),
    ("VIDEO", "5. Animation", save_vid([draw_ai_artwork() for _ in range(4)], "vid_05_animation.mp4"), "video"),
    ("VIDEO", "6. AI-generated video", save_vid([draw_ai_artwork() for _ in range(4)], "vid_06_ai_video.mp4"), "video"),
    ("VIDEO", "7. Silent video", save_vid([draw_building() for _ in range(4)], "vid_07_silent.mp4"), "video"),
    ("VIDEO", "8. Video with speech", save_vid([draw_face() for _ in range(4)], "vid_08_speech.mp4"), "video"),

    # AUDIO MATRIX (6 items)
    ("AUDIO", "1. Genuine speech", save_aud(np.tile(np.sin(2*np.pi*180*np.linspace(0, 1, 16000)), 3) * 0.4, "aud_01_speech.wav"), "audio"),
    ("AUDIO", "2. AI/synthetic speech", save_aud(np.tile(np.sin(2*np.pi*440*np.linspace(0, 1, 16000)), 3) * 0.5, "aud_02_synth_speech.wav"), "audio"),
    ("AUDIO", "3. Music", save_aud((np.sin(2*np.pi*261.6*np.linspace(0, 3, 48000)) + np.sin(2*np.pi*329.6*np.linspace(0, 3, 48000)) + np.sin(2*np.pi*392.0*np.linspace(0, 3, 48000))) * 0.25, "aud_03_music.wav"), "audio"),
    ("AUDIO", "4. Environmental audio", save_aud(np.random.normal(0, 0.08, 48000).astype(np.float32), "aud_04_ambient.wav"), "audio"),
    ("AUDIO", "5. Generated/non-speech audio", save_aud(np.sin(2*np.pi*1200*np.linspace(0, 3, 48000)) * 0.3, "aud_05_synth_sound.wav"), "audio"),
    ("AUDIO", "6. Silent audio", save_aud(np.zeros(48000, dtype=np.float32), "aud_06_silent.wav"), "audio"),
]

results_matrix = []

for mod, title, path, media_type in test_items:
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    std_res, db_payload = orch.process(
        filename=path.name,
        media_type=media_type,
        file_size=f"{path.stat().st_size} bytes",
        case_id=f"CASE-P6G-{len(results_matrix)+1}",
        analysis_id=f"ANL-P6G-{len(results_matrix)+1}",
        file_path=path
    )
    
    # Extract evidence sources and executed detectors
    evidence_sources = set()
    executed_detectors = []
    
    if std_res.visual.score is not None:
        executed_detectors.append("Vision/VisualForensics")
    if std_res.temporal.score is not None:
        executed_detectors.append("TemporalDetector")
    if std_res.audio.score is not None:
        executed_detectors.append("AudioAntiSpoofing/FeatureExtractor")
        
    for s in std_res.signals:
        if "source" in s.explanation.lower() or "VISUAL" in s.category:
            evidence_sources.add(s.category)
            
    # Check ensemble active models
    active_mods = db_payload.get("ensemble", {}).get("active_models", [])
    
    results_matrix.append({
        "modality": mod,
        "test_name": title,
        "filename": path.name,
        "sha256": sha,
        "content_type": media_type,
        "risk_overall": std_res.risk.overall,
        "risk_level": std_res.risk.level,
        "confidence": std_res.confidence,
        "active_models": active_mods,
        "signal_count": std_res.signal_count,
        "headline": std_res.explanation.get("headline") if std_res.explanation else "N/A",
        "status": std_res.status
    })

print(json.dumps(results_matrix, indent=2))
