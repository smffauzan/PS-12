import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class ForensicCase(Base):
    __tablename__ = "forensic_cases"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(64), unique=True, nullable=False, index=True)
    media_id = Column(String(64), nullable=False)
    filename = Column(String(255), nullable=False)
    media_type = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="PROCESSING")
    overall_risk = Column(Float, default=0.0)
    risk_level = Column(String(32), default="PENDING")
    confidence = Column(Float, default=0.0)
    model_consensus = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    media_items = relationship("MediaItem", back_populates="case", cascade="all, delete-orphan")
    analyses = relationship("AnalysisRecord", back_populates="case", cascade="all, delete-orphan")

class MediaItem(Base):
    __tablename__ = "media"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    media_id = Column(String(64), unique=True, nullable=False, index=True)
    case_id = Column(String(64), ForeignKey("forensic_cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(128), nullable=False)
    file_size = Column(String(64), nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    resolution = Column(String(64), nullable=True)
    duration = Column(String(64), nullable=True)
    codec = Column(String(64), nullable=True)
    metadata_json = Column(Text, default="{}")
    c2pa_status = Column(String(64), default="UNVERIFIED")
    created_at = Column(DateTime, default=utc_now)

    case = relationship("ForensicCase", back_populates="media_items")

class AnalysisRecord(Base):
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(64), unique=True, nullable=False, index=True)
    case_id = Column(String(64), ForeignKey("forensic_cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="PROCESSING")
    visual_score = Column(Float, nullable=True)
    audio_score = Column(Float, nullable=True)
    temporal_score = Column(Float, nullable=True)
    av_sync_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    consensus = Column(Float, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    model_versions = Column(Text, default="{}")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)

    case = relationship("ForensicCase", back_populates="analyses")
    signals = relationship("ForensicSignal", back_populates="analysis", cascade="all, delete-orphan")
    timeline_events = relationship("TimelineEvent", back_populates="analysis", cascade="all, delete-orphan")

class ForensicSignal(Base):
    __tablename__ = "forensic_signals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(64), ForeignKey("analyses.analysis_id", ondelete="CASCADE"), nullable=False, index=True)
    signal_name = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False, index=True)
    severity = Column(String(32), nullable=False)
    confidence = Column(Float, nullable=False)
    region = Column(String(255), nullable=True)
    timestamp = Column(String(64), nullable=True)
    technical_rationale = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    analysis = relationship("AnalysisRecord", back_populates="signals")

class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(64), ForeignKey("analyses.analysis_id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(Float, nullable=False)
    frame_number = Column(Integer, nullable=False)
    visual_score = Column(Float, nullable=False)
    audio_score = Column(Float, nullable=False)
    av_sync_score = Column(Float, nullable=False)
    severity = Column(String(32), nullable=False)
    description = Column(Text, nullable=True)

    analysis = relationship("AnalysisRecord", back_populates="timeline_events")

class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_name = Column(String(128), nullable=False)
    model_version = Column(String(64), nullable=False)
    modality = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="ACTIVE")
    created_at = Column(DateTime, default=utc_now)
