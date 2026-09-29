-- ====================================================================
-- VERITAS AI — MULTIMODAL SYNTHETIC MEDIA FORENSICS DATABASE SCHEMA
-- PostgreSQL / Supabase Compatible DDL
-- ====================================================================

-- Enable UUID extension if not enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- --------------------------------------------------------------------
-- 1. forensic_cases
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS forensic_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id VARCHAR(64) UNIQUE NOT NULL,
    media_id VARCHAR(64) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    media_type VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PROCESSING',
    overall_risk DOUBLE PRECISION DEFAULT 0.0,
    risk_level VARCHAR(32) DEFAULT 'PENDING',
    confidence DOUBLE PRECISION DEFAULT 0.0,
    model_consensus DOUBLE PRECISION DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_forensic_cases_case_id ON forensic_cases(case_id);
CREATE INDEX IF NOT EXISTS idx_forensic_cases_status ON forensic_cases(status);
CREATE INDEX IF NOT EXISTS idx_forensic_cases_created_at ON forensic_cases(created_at DESC);

-- --------------------------------------------------------------------
-- 2. media
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS media (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    media_id VARCHAR(64) UNIQUE NOT NULL,
    case_id VARCHAR(64) NOT NULL REFERENCES forensic_cases(case_id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(128) NOT NULL,
    file_size VARCHAR(64) NOT NULL,
    sha256 VARCHAR(64) NOT NULL,
    resolution VARCHAR(64),
    duration VARCHAR(64),
    codec VARCHAR(64),
    metadata_json JSONB DEFAULT '{}'::jsonb,
    c2pa_status VARCHAR(64) DEFAULT 'UNVERIFIED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_media_media_id ON media(media_id);
CREATE INDEX IF NOT EXISTS idx_media_case_id ON media(case_id);
CREATE INDEX IF NOT EXISTS idx_media_sha256 ON media(sha256);

-- --------------------------------------------------------------------
-- 3. analyses
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id VARCHAR(64) UNIQUE NOT NULL,
    case_id VARCHAR(64) NOT NULL REFERENCES forensic_cases(case_id) ON DELETE CASCADE,
    status VARCHAR(32) NOT NULL DEFAULT 'PROCESSING',
    visual_score DOUBLE PRECISION,
    audio_score DOUBLE PRECISION,
    temporal_score DOUBLE PRECISION,
    av_sync_score DOUBLE PRECISION,
    overall_score DOUBLE PRECISION,
    confidence DOUBLE PRECISION,
    consensus DOUBLE PRECISION,
    processing_time_ms INTEGER,
    model_versions JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_analyses_analysis_id ON analyses(analysis_id);
CREATE INDEX IF NOT EXISTS idx_analyses_case_id ON analyses(case_id);

-- --------------------------------------------------------------------
-- 4. forensic_signals
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS forensic_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id VARCHAR(64) NOT NULL REFERENCES analyses(analysis_id) ON DELETE CASCADE,
    signal_name VARCHAR(255) NOT NULL,
    category VARCHAR(64) NOT NULL,
    severity VARCHAR(32) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    region VARCHAR(255),
    timestamp VARCHAR(64),
    technical_rationale TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_forensic_signals_analysis_id ON forensic_signals(analysis_id);
CREATE INDEX IF NOT EXISTS idx_forensic_signals_category ON forensic_signals(category);

-- --------------------------------------------------------------------
-- 5. timeline_events
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS timeline_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id VARCHAR(64) NOT NULL REFERENCES analyses(analysis_id) ON DELETE CASCADE,
    timestamp DOUBLE PRECISION NOT NULL,
    frame_number INTEGER NOT NULL,
    visual_score DOUBLE PRECISION NOT NULL,
    audio_score DOUBLE PRECISION NOT NULL,
    av_sync_score DOUBLE PRECISION NOT NULL,
    severity VARCHAR(32) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_timeline_events_analysis_id ON timeline_events(analysis_id);
CREATE INDEX IF NOT EXISTS idx_timeline_events_timestamp ON timeline_events(timestamp);

-- --------------------------------------------------------------------
-- 6. model_registry
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS model_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(128) NOT NULL,
    model_version VARCHAR(64) NOT NULL,
    modality VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_model_name_version UNIQUE (model_name, model_version)
);

-- Seed initial models
INSERT INTO model_registry (model_name, model_version, modality, status)
VALUES
    ('VERITAS-VISION', 'v0.1', 'visual', 'ACTIVE'),
    ('VERITAS-FACEMOTION', 'v0.1', 'visual', 'ACTIVE'),
    ('VERITAS-AUDIO', 'v0.1', 'audio', 'ACTIVE'),
    ('VERITAS-TEMPORAL', 'v0.1', 'temporal', 'ACTIVE'),
    ('VERITAS-AVSYNC', 'v0.1', 'sync', 'ACTIVE'),
    ('VERITAS-FUSION', 'v0.1', 'multimodal', 'ACTIVE')
ON CONFLICT (model_name, model_version) DO NOTHING;
