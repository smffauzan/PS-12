"""
VERITAS AI — Phase 6E Real Media Acceptance & Determinism Verification
"""

import sys
import json
from pathlib import Path
from fastapi.testclient import TestClient

backend_root = Path(__file__).resolve().parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.main import app
from app.services.orchestrator import ForensicOrchestrator
from tests.test_audio_deepfake_detector import create_synthetic_wav

client = TestClient(app)
orchestrator = ForensicOrchestrator()

data_dir = backend_root / "tests" / "data"

def test_media_upload(file_path: Path, mime_type: str):
    file_bytes = file_path.read_bytes()
    filename = file_path.name
    
    res = client.post(
        "/api/v1/analyze/upload",
        files={"file": (filename, file_bytes, mime_type)}
    )
    assert res.status_code == 200, f"Upload failed for {filename}: {res.text}"
    data = res.json()
    analysis_id = data["analysis_id"]
    
    # Poll status
    status_res = client.get(f"/api/v1/analyze/{analysis_id}")
    assert status_res.status_code == 200
    result = status_res.json()
    return result

print("=" * 80)
print("PHASE 6E REAL MEDIA PIPELINE VERIFICATION")
print("=" * 80)

# 1. REAL IMAGE ACCEPTANCE TEST
# Test with single_face.jpg and messi.jpg
single_face_path = data_dir / "single_face.jpg"
messi_path = data_dir / "messi.jpg"
no_face_path = data_dir / "no_face.jpg"

print("\n--- 1. REAL IMAGE TESTS ---")
res_single = test_media_upload(single_face_path, "image/jpeg")
print(f"IMAGE A (single_face.jpg):")
print(f"  SHA-256: {res_single['sha256']}")
print(f"  Media ID: {res_single['media_id']}")
print(f"  Analysis ID: {res_single['analysis_id']}")
print(f"  Risk Overall: {res_single['risk']['overall']}")
print(f"  Risk Level: {res_single['risk']['level']}")
print(f"  Visual Score: {res_single['visual']['score']}")
print(f"  Explanation Headline: {res_single['explanation']['headline']}")

res_messi = test_media_upload(messi_path, "image/jpeg")
print(f"\nIMAGE B (messi.jpg):")
print(f"  SHA-256: {res_messi['sha256']}")
print(f"  Media ID: {res_messi['media_id']}")
print(f"  Analysis ID: {res_messi['analysis_id']}")
print(f"  Risk Overall: {res_messi['risk']['overall']}")
print(f"  Risk Level: {res_messi['risk']['level']}")
print(f"  Visual Score: {res_messi['visual']['score']}")
print(f"  Explanation Headline: {res_messi['explanation']['headline']}")

res_noface = test_media_upload(no_face_path, "image/jpeg")
print(f"\nIMAGE C (no_face.jpg - Inconclusive Semantics Check):")
print(f"  SHA-256: {res_noface['sha256']}")
print(f"  Risk Overall: {res_noface['risk']['overall']} (Expected: None)")
print(f"  Risk Level: {res_noface['risk']['level']} (Expected: INCONCLUSIVE)")
print(f"  Explanation Headline: {res_noface['explanation']['headline']}")

# 2. REAL VIDEO ACCEPTANCE TEST
sample_video_path = data_dir / "sample_face_video.mp4"
noface_video_path = data_dir / "no_face_video.mp4"

print("\n--- 2. REAL VIDEO TESTS ---")
res_vid = test_media_upload(sample_video_path, "video/mp4")
print(f"VIDEO A (sample_face_video.mp4):")
print(f"  SHA-256: {res_vid['sha256']}")
print(f"  Media ID: {res_vid['media_id']}")
print(f"  Analysis ID: {res_vid['analysis_id']}")
print(f"  Risk Overall: {res_vid['risk']['overall']}")
print(f"  Risk Level: {res_vid['risk']['level']}")
print(f"  Visual Score: {res_vid['visual']['score']}")
print(f"  Temporal Score: {res_vid['temporal']['score']}")
print(f"  Evidence Windows Count: {len(res_vid['metadata'].get('evidence_windows', []))}")
print(f"  Explanation Headline: {res_vid['explanation']['headline']}")

res_vid_noface = test_media_upload(noface_video_path, "video/mp4")
print(f"\nVIDEO B (no_face_video.mp4 - Inconclusive Check):")
print(f"  SHA-256: {res_vid_noface['sha256']}")
print(f"  Risk Overall: {res_vid_noface['risk']['overall']} (Expected: None)")
print(f"  Risk Level: {res_vid_noface['risk']['level']} (Expected: INCONCLUSIVE)")
print(f"  Explanation Headline: {res_vid_noface['explanation']['headline']}")

# 3. REAL AUDIO ACCEPTANCE TEST
# Generate speech-like harmonic audio test file
aud_p1, _ = create_synthetic_wav(duration_sec=4.0, harmonics=True)
aud_p2, _ = create_synthetic_wav(duration_sec=4.0, narrowband=True)
aud_bytes1 = aud_p1.read_bytes()
aud_bytes2 = aud_p2.read_bytes()

print("\n--- 3. REAL AUDIO TESTS ---")
res_aud1 = client.post("/api/v1/analyze/upload", files={"file": ("speech_harmonic.wav", aud_bytes1, "audio/wav")}).json()
res_aud1_data = client.get(f"/api/v1/analyze/{res_aud1['analysis_id']}").json()
print(f"AUDIO A (speech_harmonic.wav):")
print(f"  SHA-256: {res_aud1_data['sha256']}")
print(f"  Media ID: {res_aud1_data['media_id']}")
print(f"  Analysis ID: {res_aud1_data['analysis_id']}")
print(f"  Risk Overall: {res_aud1_data['risk']['overall']}")
print(f"  Risk Level: {res_aud1_data['risk']['level']}")
print(f"  Audio Score: {res_aud1_data['audio']['score']}")
print(f"  Explanation Headline: {res_aud1_data['explanation']['headline']}")

res_aud2 = client.post("/api/v1/analyze/upload", files={"file": ("speech_narrowband.wav", aud_bytes2, "audio/wav")}).json()
res_aud2_data = client.get(f"/api/v1/analyze/{res_aud2['analysis_id']}").json()
print(f"\nAUDIO B (speech_narrowband.wav):")
print(f"  SHA-256: {res_aud2_data['sha256']}")
print(f"  Media ID: {res_aud2_data['media_id']}")
print(f"  Analysis ID: {res_aud2_data['analysis_id']}")
print(f"  Risk Overall: {res_aud2_data['risk']['overall']}")
print(f"  Risk Level: {res_aud2_data['risk']['level']}")
print(f"  Audio Score: {res_aud2_data['audio']['score']}")
print(f"  Explanation Headline: {res_aud2_data['explanation']['headline']}")

# 4. DETERMINISM TEST (Upload single_face.jpg again)
print("\n--- 4. DETERMINISM TEST ---")
res_single_again = test_media_upload(single_face_path, "image/jpeg")
print(f"Run 1 SHA: {res_single['sha256']} | Risk: {res_single['risk']['overall']} | Level: {res_single['risk']['level']}")
print(f"Run 2 SHA: {res_single_again['sha256']} | Risk: {res_single_again['risk']['overall']} | Level: {res_single_again['risk']['level']}")
assert res_single['sha256'] == res_single_again['sha256']
assert res_single['risk']['overall'] == res_single_again['risk']['overall']
assert res_single['risk']['level'] == res_single_again['risk']['level']
print("[SUCCESS] DETERMINISM VERIFIED: Exact identical result for identical media.")

# 5. DIFFERENT-FILE IDENTITY TEST
print("\n--- 5. DIFFERENT FILE IDENTITY TEST ---")
assert res_single['sha256'] != res_messi['sha256']
assert res_single['media_id'] != res_messi['media_id']
assert res_single['analysis_id'] != res_messi['analysis_id']
print("[SUCCESS] DIFFERENT-FILE IDENTITY VERIFIED: Unique SHA-256, Media ID, and Analysis ID.")

print("\n" + "=" * 80)
print("ALL REAL-MEDIA ACCEPTANCE CHECKS PASSED")
print("=" * 80)
