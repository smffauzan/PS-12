import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend root
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "").strip()

    # Supabase / PostgreSQL Credentials
    DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "").strip()
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "").strip()
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    # Storage
    STORE_MEDIA: bool = os.getenv("STORE_MEDIA", "false").lower() in ("true", "1", "yes")
    SUPABASE_STORAGE_BUCKET: str = os.getenv("SUPABASE_STORAGE_BUCKET", "forensic-media")

    # Security
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "500"))
    ALLOWED_MIME_TYPES: list = [
        m.strip() for m in os.getenv(
            "ALLOWED_MIME_TYPES",
            "video/mp4,video/quicktime,video/x-matroska,image/jpeg,image/png,image/webp,audio/mpeg,audio/wav,audio/mp4"
        ).split(",") if m.strip()
    ]

settings = Settings()
