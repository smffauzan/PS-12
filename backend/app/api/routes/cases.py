import uuid
import json
import time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repository import ForensicRepository
from app.schemas.cases import CaseCreateSchema, CaseSummarySchema, CaseListResponse
from app.services.orchestrator import ForensicOrchestrator
from app.services.media_processor import media_processor, temporary_media_workspace, MediaValidationError
from app.core.security import sanitize_filename
from app.core.logging_config import forensic_logger

router = APIRouter(prefix="/cases", tags=["Cases"])
orchestrator = ForensicOrchestrator()

# In-memory fast cache for active UI objects
CASES_CACHE: Dict[str, Any] = {}

def _safe_json_loads(val: Any) -> Dict[str, Any]:
    if isinstance(val, dict):
        return val
    if isinstance(val, str) and val.strip():
        try:
            return json.loads(val)
        except Exception:
            return {}
    return {}

def _seed_default_case(repo: ForensicRepository):
    """Seeds the initial benchmark forensic case into the persistent database if not present."""
    default_case_id = "CASE VX-04291"
    existing = repo.get_case(default_case_id)
    if not existing:
        analysis_id = "ANL-89412"
        std_res, db_payload = orchestrator.process(
            filename="breaking_news_042.mp4",
            media_type="video",
            file_size="48.2 MB",
            case_id=default_case_id,
            analysis_id=analysis_id
        )

        repo.create_case(
            case_id=default_case_id,
            media_id=std_res.media_id,
            filename=std_res.filename,
            media_type=std_res.media_type,
            status="COMPLETE"
        )
        repo.update_case_results(
            case_id=default_case_id,
            status="COMPLETE",
            overall_risk=std_res.risk.overall,
            risk_level=std_res.risk.level,
            confidence=std_res.confidence,
            model_consensus=std_res.consensus
        )
        repo.create_media(
            media_id=std_res.media_id,
            case_id=default_case_id,
            filename=std_res.filename,
            mime_type=std_res.metadata.get("mimeType", "video/mp4"),
            file_size=std_res.metadata.get("bitrate", "48.2 MB"),
            sha256=std_res.sha256,
            resolution=std_res.metadata.get("resolution", "1920x1080"),
            duration=std_res.metadata.get("duration", "00:32.4"),
            codec=std_res.metadata.get("codec", "H.264 / AVC"),
            metadata_json=std_res.metadata,
            c2pa_status=std_res.provenance.status
        )
        repo.create_analysis(analysis_id=analysis_id, case_id=default_case_id, status="COMPLETE")
        repo.complete_analysis(
            analysis_id=analysis_id,
            visual_score=db_payload["visual_score"],
            audio_score=db_payload["audio_score"],
            temporal_score=db_payload["temporal_score"],
            av_sync_score=db_payload["av_sync_score"],
            overall_score=db_payload["overall_score"],
            confidence=db_payload["confidence"],
            consensus=db_payload["consensus"],
            processing_time_ms=db_payload["processing_time_ms"],
            model_versions=db_payload["model_versions"]
        )
        repo.add_signals(analysis_id, db_payload["signals"])
        repo.add_timeline_events(analysis_id, db_payload["timeline"])
        CASES_CACHE[default_case_id] = std_res.dict()

@router.post("")
def create_case(req: CaseCreateSchema, db: Session = Depends(get_db)):
    repo = ForensicRepository(db)
    clean_filename = sanitize_filename(req.filename)
    case_id = req.case_id or f"CASE VX-{uuid.uuid4().hex[:5].upper()}"
    analysis_id = f"ANL-{uuid.uuid4().hex[:6].upper()}"
    media_id = f"MED-{uuid.uuid4().hex[:5].upper()}-X"

    # 1. Log and create case record
    forensic_logger.case_created(case_id, media_id, clean_filename)
    forensic_logger.media_received(case_id, media_id, clean_filename, f"{req.media_type}/unknown", req.file_size or "48.2 MB")
    forensic_logger.analysis_started(case_id, analysis_id)

    db_case = repo.create_case(
        case_id=case_id,
        media_id=media_id,
        filename=clean_filename,
        media_type=req.media_type,
        status="PROCESSING"
    )

    repo.create_analysis(analysis_id=analysis_id, case_id=case_id, status="PROCESSING")

    try:
        # Run orchestrator
        std_res, db_payload = orchestrator.process(
            filename=clean_filename,
            media_type=req.media_type,
            file_size=req.file_size or "48.2 MB",
            case_id=case_id,
            analysis_id=analysis_id
        )

        # Save media
        repo.create_media(
            media_id=std_res.media_id,
            case_id=case_id,
            filename=clean_filename,
            mime_type=std_res.metadata.get("mimeType", "video/mp4"),
            file_size=req.file_size or "48.2 MB",
            sha256=std_res.sha256,
            resolution=std_res.metadata.get("resolution", "1920x1080"),
            duration=std_res.metadata.get("duration", "00:32.4"),
            codec=std_res.metadata.get("codec", "H.264 / AVC"),
            metadata_json=std_res.metadata,
            c2pa_status=std_res.provenance.status
        )

        # Complete analysis
        repo.complete_analysis(
            analysis_id=analysis_id,
            visual_score=db_payload["visual_score"],
            audio_score=db_payload["audio_score"],
            temporal_score=db_payload["temporal_score"],
            av_sync_score=db_payload["av_sync_score"],
            overall_score=db_payload["overall_score"],
            confidence=db_payload["confidence"],
            consensus=db_payload["consensus"],
            processing_time_ms=db_payload["processing_time_ms"],
            model_versions=db_payload["model_versions"]
        )

        # Save signals & timeline
        repo.add_signals(analysis_id, db_payload["signals"])
        repo.add_timeline_events(analysis_id, db_payload["timeline"])

        # Update case
        repo.update_case_results(
            case_id=case_id,
            status="COMPLETE",
            overall_risk=std_res.risk.overall,
            risk_level=std_res.risk.level,
            confidence=std_res.confidence,
            model_consensus=std_res.consensus
        )

        forensic_logger.analysis_completed(case_id, analysis_id, std_res.risk.overall, db_payload["processing_time_ms"])
        CASES_CACHE[case_id] = std_res.dict()
        return std_res

    except Exception as exc:
        repo.fail_analysis(analysis_id, str(exc))
        repo.update_case_results(
            case_id=case_id,
            status="FAILED",
            overall_risk=0.0,
            risk_level="FAILED",
            confidence=0.0,
            model_consensus=0.0
        )
        forensic_logger.analysis_failed(case_id, analysis_id, str(exc))
        raise HTTPException(status_code=500, detail=f"Forensic analysis failed: {str(exc)}")

@router.post("/upload")
async def create_case_upload(
    file: UploadFile = File(...),
    case_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    repo = ForensicRepository(db)
    file_bytes = await file.read()
    clean_filename = sanitize_filename(file.filename)

    try:
        clean_filename, validated_mime = media_processor.validate_media(
            filename=clean_filename,
            mime_type=file.content_type,
            file_size_bytes=len(file_bytes),
            header_bytes=file_bytes[:32]
        )
    except MediaValidationError as err:
        raise HTTPException(
            status_code=415 if "MIME" in err.error_code or "UNSUPPORTED" in err.error_code else 400,
            detail={"error_code": err.error_code, "message": err.message}
        )

    media_type = "image" if validated_mime.startswith("image/") else "audio" if validated_mime.startswith("audio/") else "video"
    case_id_val = case_id or f"CASE VX-{uuid.uuid4().hex[:5].upper()}"
    analysis_id = f"ANL-{uuid.uuid4().hex[:6].upper()}"
    media_id = f"MED-{uuid.uuid4().hex[:5].upper()}-X"

    forensic_logger.case_created(case_id_val, media_id, clean_filename)
    forensic_logger.media_received(case_id_val, media_id, clean_filename, validated_mime, media_processor.format_file_size(len(file_bytes)))
    forensic_logger.analysis_started(case_id_val, analysis_id)

    db_case = repo.create_case(
        case_id=case_id_val,
        media_id=media_id,
        filename=clean_filename,
        media_type=media_type,
        status="PROCESSING"
    )

    repo.create_analysis(analysis_id=analysis_id, case_id=case_id_val, status="PROCESSING")

    try:
        with temporary_media_workspace() as tmp_dir:
            tmp_path = tmp_dir / clean_filename
            tmp_path.write_bytes(file_bytes)

            std_res, db_payload = orchestrator.process(
                filename=clean_filename,
                media_type=media_type,
                file_size=media_processor.format_file_size(len(file_bytes)),
                case_id=case_id_val,
                analysis_id=analysis_id,
                file_path=tmp_path
            )

        repo.create_media(
            media_id=std_res.media_id,
            case_id=case_id_val,
            filename=clean_filename,
            mime_type=validated_mime,
            file_size=media_processor.format_file_size(len(file_bytes)),
            sha256=std_res.sha256,
            resolution=std_res.metadata.get("resolution", "1920x1080"),
            duration=std_res.metadata.get("duration", "00:30.00"),
            codec=std_res.metadata.get("codec", "H.264 / AVC"),
            metadata_json=std_res.metadata,
            c2pa_status=std_res.provenance.status
        )

        repo.complete_analysis(
            analysis_id=analysis_id,
            visual_score=db_payload["visual_score"],
            audio_score=db_payload["audio_score"],
            temporal_score=db_payload["temporal_score"],
            av_sync_score=db_payload["av_sync_score"],
            overall_score=db_payload["overall_score"],
            confidence=db_payload["confidence"],
            consensus=db_payload["consensus"],
            processing_time_ms=db_payload["processing_time_ms"],
            model_versions=db_payload["model_versions"]
        )

        repo.add_signals(analysis_id, db_payload["signals"])
        repo.add_timeline_events(analysis_id, db_payload["timeline"])

        repo.update_case_results(
            case_id=case_id_val,
            status="COMPLETE",
            overall_risk=std_res.risk.overall,
            risk_level=std_res.risk.level,
            confidence=std_res.confidence,
            model_consensus=std_res.consensus
        )

        forensic_logger.analysis_completed(case_id_val, analysis_id, std_res.risk.overall, db_payload["processing_time_ms"])
        CASES_CACHE[case_id_val] = std_res.dict()
        return std_res

    except Exception as exc:
        repo.fail_analysis(analysis_id, str(exc))
        repo.update_case_results(
            case_id=case_id_val,
            status="FAILED",
            overall_risk=0.0,
            risk_level="FAILED",
            confidence=0.0,
            model_consensus=0.0
        )
        forensic_logger.analysis_failed(case_id_val, analysis_id, str(exc))
        raise HTTPException(status_code=500, detail=f"Forensic upload case creation failed: {str(exc)}")

@router.get("", response_model=CaseListResponse)
def list_cases(db: Session = Depends(get_db)):
    repo = ForensicRepository(db)
    _seed_default_case(repo)
    stored_cases = repo.list_cases(limit=50)

    cases_summary: List[CaseSummarySchema] = []
    for c in stored_cases:
        created_str = c.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if c.created_at else "2026-09-29 14:22:08 UTC"
        cases_summary.append(CaseSummarySchema(
            case_id=c.case_id,
            media_id=c.media_id,
            filename=c.filename,
            media_type=c.media_type,
            risk_score=int(c.overall_risk or 0),
            risk_tier=c.risk_level or "PENDING",
            confidence=int(c.confidence or 0),
            consensus=int(c.model_consensus or 0),
            signal_count=5,
            timestamp=created_str,
            status=c.status
        ))

    return CaseListResponse(cases=cases_summary, total=len(cases_summary))

@router.get("/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db)):
    # Check cache first for rapid full-graph response
    if case_id in CASES_CACHE:
        return CASES_CACHE[case_id]

    repo = ForensicRepository(db)
    _seed_default_case(repo)
    case = repo.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Forensic case not found")

    # Reconstruct complete case representation
    media = repo.get_media_by_case(case_id)
    analysis = repo.get_analysis_by_case(case_id)

    signals = []
    timeline = []
    if analysis:
        signals_models = repo.get_signals_by_analysis(analysis.analysis_id)
        signals = [
            {
                "id": s.id,
                "name": s.signal_name,
                "category": s.category,
                "severity": s.severity,
                "confidence": s.confidence,
                "affectedRegionOrTime": s.region or s.timestamp or "Visual contour",
                "explanation": s.technical_rationale
            }
            for s in signals_models
        ]
        timeline_models = repo.get_timeline_by_analysis(analysis.analysis_id)
        timeline = [
            {
                "id": t.id,
                "timestampSec": t.timestamp,
                "formattedTime": f"00:{int(t.timestamp):02d}.0",
                "frameNumber": t.frame_number,
                "visualScore": t.visual_score,
                "audioScore": t.audio_score,
                "avSyncScore": t.av_sync_score,
                "overallRisk": t.visual_score,
                "severity": t.severity,
                "explanation": t.description
            }
            for t in timeline_models
        ]

    # Return full case dictionary
    full_case = {
        "case_id": case.case_id,
        "media_id": case.media_id,
        "filename": case.filename,
        "media_type": case.media_type,
        "status": case.status,
        "risk": {
            "overall": case.overall_risk,
            "level": case.risk_level
        },
        "confidence": case.confidence,
        "consensus": case.model_consensus,
        "signal_count": len(signals) or 5,
        "visual": {"score": analysis.visual_score if analysis else 85, "signals": [s for s in signals if s["category"] == "visual"]},
        "audio": {"score": analysis.audio_score if analysis else 73, "signals": [s for s in signals if s["category"] == "audio"]},
        "temporal": {"score": analysis.temporal_score if analysis else 84, "signals": [s for s in signals if s["category"] == "temporal"]},
        "av_sync": {"score": analysis.av_sync_score if analysis else 81, "signals": [s for s in signals if s["category"] == "sync"]},
        "signals": signals,
        "timeline": timeline,
        "metadata": _safe_json_loads(media.metadata_json) if media and media.metadata_json else {}
    }
    CASES_CACHE[case_id] = full_case
    return full_case
