from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json

from app.core.config import settings
from app.db.database import init_db, check_database_health, check_storage_health
from app.api.routes.analysis import router as analysis_router
from app.api.routes.cases import router as cases_router
from app.api.routes.provenance import router as provenance_router
from app.api.routes.reports import router as reports_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and seed registry
    init_db()
    yield

app = FastAPI(
    title="VERITAS AI - Multimodal Synthetic Media Forensics API",
    description="Backend AI Orchestrator, Persistent Database, and Model Adapter Interface for VERITAS AI",
    version="v0.9.0-PERSISTENCE",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 routes
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(cases_router, prefix="/api/v1")
app.include_router(provenance_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    db_status = check_database_health()
    storage_status = check_storage_health()

    return {
        "api": "online",
        "database": db_status,
        "models": "ready",
        "storage": storage_status,
        "engine": "VERITAS AI FORENSIC ORCHESTRATOR",
        "version": "v0.9.0-PERSISTENCE",
        "registered_models": {
            "vision": "VERITAS-VISION-v0.1",
            "audio": "VERITAS-AUDIO-v0.1",
            "temporal": "VERITAS-TEMPORAL-v0.1",
            "av_sync": "VERITAS-AVSYNC-v0.1",
            "fusion": "VERITAS-FUSION-v0.1"
        },
        "store_media": settings.STORE_MEDIA,
        "environment": settings.ENVIRONMENT
    }

@app.websocket("/ws/analysis/{analysis_id}")
async def analysis_websocket(websocket: WebSocket, analysis_id: str):
    await websocket.accept()
    stages = [
        ("INGEST", 8),
        ("HASH", 16),
        ("METADATA", 24),
        ("PROVENANCE", 32),
        ("FACE DETECTION", 40),
        ("VISUAL ANALYSIS", 48),
        ("AUDIO ANALYSIS", 56),
        ("TEMPORAL ANALYSIS", 64),
        ("A/V SYNC", 72),
        ("MODEL CONSENSUS", 80),
        ("RISK ENGINE", 90),
        ("EVIDENCE GENERATION", 100),
    ]
    try:
        for stage_name, progress in stages:
            await websocket.send_text(json.dumps({
                "analysis_id": analysis_id,
                "stage": stage_name,
                "progress": progress,
                "status": "PROCESSING" if progress < 100 else "COMPLETE"
            }))
            await asyncio.sleep(0.4)
    except WebSocketDisconnect:
        pass
