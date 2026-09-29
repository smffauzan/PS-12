import sys
import os
import cv2
import numpy as np
import scipy.io.wavfile as wavfile
from pathlib import Path

# Add backend to path
sys.path.insert(0, r"d:\PS12\backend")

from app.services.orchestrator import ForensicOrchestrator
from app.services.media_processor import temporary_media_workspace

def test_pipeline():
    orchestrator = ForensicOrchestrator()
    print("Orchestrator loaded successfully.")
    print(f"Image detector: {type(orchestrator.image_detector).__name__} (is_mock={getattr(orchestrator.image_detector, 'is_mock', True)})")
    print(f"Video detector: {type(orchestrator.video_detector).__name__} (is_mock={getattr(orchestrator.video_detector, 'is_mock', True)})")
    print(f"Audio detector: {type(orchestrator.audio_deepfake_detector).__name__} (is_mock={getattr(orchestrator.audio_deepfake_detector, 'is_mock', True)})")
    print(f"Temporal detector: {type(orchestrator.temporal_detector).__name__} (is_mock={getattr(orchestrator.temporal_detector, 'is_mock', True)})")

    with temporary_media_workspace() as tmp_dir:
        # 1. Create Image A: Blank/Random noise (No face)
        img_a_path = tmp_dir / "image_a_noface.jpg"
        img_a = np.random.randint(0, 255, (400, 400, 3), dtype=np.uint8)
        cv2.imwrite(str(img_a_path), img_a)

        # 2. Create Image B: Synthetic geometric drawing
        img_b_path = tmp_dir / "image_b_geom.png"
        img_b = np.zeros((400, 400, 3), dtype=np.uint8)
        cv2.circle(img_b, (200, 200), 80, (255, 255, 255), -1)
        cv2.imwrite(str(img_b_path), img_b)

        # 3. Create Audio A: Pure Sine Wave 440 Hz
        aud_a_path = tmp_dir / "audio_a_sine.wav"
        sr = 16000
        t = np.linspace(0, 3.0, int(sr * 3.0), endpoint=False)
        sig_a = (0.5 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        wavfile.write(str(aud_a_path), sr, sig_a)

        # 4. Create Audio B: Chirp signal (sweeping frequency 200 to 4000 Hz)
        aud_b_path = tmp_dir / "audio_b_chirp.wav"
        f_inst = np.linspace(200, 4000, len(t))
        phase = 2 * np.pi * np.cumsum(f_inst) / sr
        sig_b = (0.5 * np.sin(phase) * 32767).astype(np.int16)
        wavfile.write(str(aud_b_path), sr, sig_b)

        # 5. Create Video A: 2-second moving circle
        vid_a_path = tmp_dir / "video_a.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_a = cv2.VideoWriter(str(vid_a_path), fourcc, 10.0, (200, 200))
        for i in range(20):
            frame = np.zeros((200, 200, 3), dtype=np.uint8)
            cv2.circle(frame, (30 + i * 5, 100), 20, (0, 255, 0), -1)
            out_a.write(frame)
        out_a.release()

        # 6. Create Video B: 3-second noise video
        vid_b_path = tmp_dir / "video_b.mp4"
        out_b = cv2.VideoWriter(str(vid_b_path), fourcc, 10.0, (200, 200))
        for i in range(30):
            frame = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
            out_b.write(frame)
        out_b.release()

        print("\n--- RUNNING ORCHESTRATOR ANALYSIS ON 6 DISTINCT FILES ---")
        
        files_to_test = [
            ("image_a_noface.jpg", "image", img_a_path),
            ("image_b_geom.png", "image", img_b_path),
            ("audio_a_sine.wav", "audio", aud_a_path),
            ("audio_b_chirp.wav", "audio", aud_b_path),
            ("video_a.mp4", "video", vid_a_path),
            ("video_b.mp4", "video", vid_b_path)
        ]

        for fname, mtype, fpath in files_to_test:
            res, db = orchestrator.process(
                filename=fname,
                media_type=mtype,
                file_size="1.0 MB",
                case_id=f"CASE-TEST-{fname}",
                analysis_id=f"ANL-TEST-{fname}",
                file_path=fpath
            )
            print(f"\nFile: {fname} [{mtype.upper()}]")
            print(f"  SHA-256: {res.sha256[:16]}...")
            print(f"  Overall Risk: {res.risk.overall}% ({res.risk.level})")
            print(f"  Confidence: {res.confidence}%")
            print(f"  Visual Score: {res.visual.score} | Audio: {res.audio.score} | Temporal: {res.temporal.score}")
            print(f"  Explanation Headline: {res.explanation.get('headline') if res.explanation else 'N/A'}")
            print(f"  Explanation Summary: {res.explanation.get('summary') if res.explanation else 'N/A'}")
            print(f"  Number of reasons: {len(res.explanation.get('reasons', [])) if res.explanation else 0}")
            for r in (res.explanation.get('reasons', []) if res.explanation else []):
                print(f"    - [{r.get('category')}]: {r.get('title')} -> {r.get('description')}")

if __name__ == "__main__":
    test_pipeline()
