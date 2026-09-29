import re
import os
import tempfile
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
from fastapi import HTTPException, status
from app.core.config import settings

def sanitize_filename(filename: str) -> str:
    """Sanitizes user filename by removing dangerous directory traversal characters."""
    if not filename:
        return "unnamed_media_asset.bin"
    # Keep only alphanumeric, hyphen, underscore, dot
    clean_name = os.path.basename(filename)
    clean_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', clean_name)
    # Prevent leading dots / hidden files
    clean_name = clean_name.lstrip('.')
    return clean_name or "media_asset.bin"

def validate_media_upload(filename: str, mime_type: str, file_size_bytes: int):
    """Validates file-size, MIME-type, and filename security controls."""
    # Validate MIME type
    if mime_type.lower() not in [m.lower() for m in settings.ALLOWED_MIME_TYPES]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "error_code": "ERR_UNSUPPORTED_MIME_TYPE",
                "message": f"MIME type '{mime_type}' is not supported for forensic inspection.",
                "allowed_types": settings.ALLOWED_MIME_TYPES
            }
        )

    # Validate file size
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size_bytes > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error_code": "ERR_PAYLOAD_TOO_LARGE",
                "message": f"Media file size ({file_size_bytes / (1024*1024):.1f} MB) exceeds maximum permitted intake limit ({settings.MAX_UPLOAD_SIZE_MB} MB)."
            }
        )

@contextmanager
def temporary_media_file(suffix: str = ".tmp") -> Generator[Path, None, None]:
    """Provides a managed temporary file that is guaranteed to be deleted upon context exit."""
    fd, temp_path_str = tempfile.mkstemp(suffix=suffix, prefix="veritas_forensic_")
    os.close(fd)
    temp_path = Path(temp_path_str)
    try:
        yield temp_path
    finally:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except Exception:
            pass
