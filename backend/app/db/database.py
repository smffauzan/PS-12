import os
from pathlib import Path
from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

Base = declarative_base()

# Database Connection Selection
# If user provided DATABASE_URL (Supabase PostgreSQL), connect to it.
# Otherwise, fall back to SQLite for persistent local development.
db_url = settings.DATABASE_URL
using_local_sqlite = False

import re
import urllib.parse

def _normalize_db_url(raw_url: str) -> str:
    """Normalizes PostgreSQL connection URI for SQLAlchemy and psycopg2."""
    if not raw_url:
        return raw_url
    
    # Handle standard URI matching: postgresql://user:pass@host:port/dbname
    m = re.match(r'^(?:postgresql|postgres)(?:\+psycopg2)?://([^:]+):(.*)@([^@:]+)(:\d+)?/(.*)$', raw_url)
    if m:
        user, raw_pass, host, port, db_name = m.groups()
        # Remove surrounding placeholder brackets if present
        if raw_pass.startswith('[') and raw_pass.endswith(']'):
            raw_pass = raw_pass[1:-1]
        
        # URL-unquote first to avoid double encoding, then quote cleanly
        unquoted = urllib.parse.unquote(raw_pass)
        encoded_pass = urllib.parse.quote(unquoted, safe='')
        port_str = port or ':5432'
        return f"postgresql+psycopg2://{user}:{encoded_pass}@{host}{port_str}/{db_name}"

    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return raw_url

if not db_url or "YOUR-PASSWORD" in db_url:
    # Use local persistent sqlite file in backend directory
    backend_dir = Path(__file__).resolve().parent.parent.parent
    sqlite_path = backend_dir / "veritas.db"
    db_url = f"sqlite:///{sqlite_path.as_posix()}"
    using_local_sqlite = True
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False}
    )
else:
    # Supabase PostgreSQL
    normalized_url = _normalize_db_url(db_url)
    engine = create_engine(
        normalized_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Optional Supabase Client initialization
supabase_client = None
if settings.SUPABASE_URL and settings.SUPABASE_KEY and "YOUR-SUPABASE" not in settings.SUPABASE_URL:
    try:
        from supabase import create_client, Client
        supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    except Exception as e:
        print(f"[VERITAS-DB] Warning: Supabase client failed to initialize: {e}")

def get_db() -> Generator[Session, None, None]:
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes schema and seeds initial model registry."""
    from app.db import models  # noqa
    Base.metadata.create_all(bind=engine)
    
    # Seed default model registry if empty
    db = SessionLocal()
    try:
        existing = db.query(models.ModelRegistry).first()
        if not existing:
            default_models = [
                models.ModelRegistry(model_name="VERITAS-VISION", model_version="v0.1", modality="visual", status="ACTIVE"),
                models.ModelRegistry(model_name="VERITAS-FACEMOTION", model_version="v0.1", modality="visual", status="ACTIVE"),
                models.ModelRegistry(model_name="VERITAS-AUDIO", model_version="v0.1", modality="audio", status="ACTIVE"),
                models.ModelRegistry(model_name="VERITAS-TEMPORAL", model_version="v0.1", modality="temporal", status="ACTIVE"),
                models.ModelRegistry(model_name="VERITAS-AVSYNC", model_version="v0.1", modality="sync", status="ACTIVE"),
                models.ModelRegistry(model_name="VERITAS-FUSION", model_version="v0.1", modality="multimodal", status="ACTIVE"),
            ]
            db.add_all(default_models)
            db.commit()
    except Exception as err:
        db.rollback()
        print(f"[VERITAS-DB] Model registry seeding warning: {err}")
    finally:
        db.close()

def check_database_health() -> str:
    """Verifies live database connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        if using_local_sqlite:
            return "online (local persistence // Supabase unconfigured in .env)"
        return "online (PostgreSQL / Supabase connected)"
    except Exception as e:
        return f"offline ({str(e)})"

def check_storage_health() -> str:
    """Checks media storage system status."""
    if settings.STORE_MEDIA:
        if supabase_client:
            return "ready (Supabase Storage connected)"
        return "degraded (STORE_MEDIA=true but Supabase credentials unconfigured)"
    return "ready (ephemeral local processing // STORE_MEDIA=false)"
