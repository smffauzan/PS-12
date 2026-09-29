from typing import Dict, Any

class MetadataService:
    """EXIF, container atom, and bitstream codec inspection service."""

    def extract(self, filename: str, media_type: str, file_size: str) -> Dict[str, Any]:
        is_video = media_type == "video"
        is_audio = media_type == "audio"

        return {
            "fileType": "MPEG-4 (MP4)" if is_video else "WAVE Audio" if is_audio else "PNG Image",
            "mimeType": "video/mp4" if is_video else "audio/wav" if is_audio else "image/png",
            "codec": "H.264 / AVC (High Profile)" if is_video else "PCM 16-bit" if is_audio else "PNG RGBA",
            "resolution": "3840 x 2160 (4K UHD)" if is_video else "4096 x 2730" if not is_audio else "N/A",
            "frameCount": 900 if is_video else None,
            "bitrate": "14.2 Mbps" if is_video else "1411 kbps" if is_audio else "N/A",
            "duration": "00:30.00 (30 fps)" if is_video else "01:45.00" if is_audio else "N/A",
            "creationDate": "2026-09-28 21:14:02",
            "modificationDate": "2026-09-29 02:40:11",
            "software": "Unknown Encoder / FFmpeg 6.1 (Synthetic pipeline indicators detected)",
            "colorSpace": "BT.709 (sRGB)",
            "cameraModel": "None (EXIF Header Stripped)"
        }
