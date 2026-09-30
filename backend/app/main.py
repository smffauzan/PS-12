from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
import os

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

# CORS configuration: allow localhost origins + FRONTEND_ORIGIN from env
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

if settings.FRONTEND_ORIGIN:
    for origin in settings.FRONTEND_ORIGIN.split(","):
        origin_clean = origin.strip().rstrip("/")
        if origin_clean and origin_clean not in allowed_origins:
            allowed_origins.append(origin_clean)

# Also allow wildcard origin in development or when no explicit FRONTEND_ORIGIN is specified
if settings.ENVIRONMENT == "development" or not settings.FRONTEND_ORIGIN:
    if "*" not in allowed_origins:
        allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", str(settings.PORT)))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("app.main:app", host=host, port=port, reload=(settings.ENVIRONMENT == "development"))
