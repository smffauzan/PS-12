from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
import uuid
import time
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repository import ForensicRepository
from app.schemas.analysis import AnalysisRequestSchema, AnalysisResponseSchema
from app.services.orchestrator import ForensicOrchestrator
from app.services.media_processor import media_processor, temporary_media_workspace, MediaValidationError
from app.core.security import sanitize_filename
from app.core.logging_config import forensic_logger

router = APIRouter(prefix="/analyze", tags=["Analysis"])
orchestrator = ForensicOrchestrator()

# Fast in-memory cache for polling results
ACTIVE_ANALYSES: Dict[str, Dict[str, Any]] = {}

@router.post("", response_model=AnalysisResponseSchema)
def start_analysis(req: AnalysisRequestSchema, db: Session = Depends(get_db)):
    repo = ForensicRepository(db)
    analysis_id = f"ANL-{uuid.uuid4().hex[:6].upper()}"
    case_id = req.case_id or f"CASE VX-{uuid.uuid4().hex[:5].upper()}"
    media_id = f"MED-{uuid.uuid4().hex[:5].upper()}-X"
    clean_filename = sanitize_filename(req.filename)

    # 1. Log and create database records with status = PROCESSING
    forensic_logger.case_created(case_id, media_id, clean_filename)
    forensic_logger.media_received(case_id, media_id, clean_filename, f"{req.media_type}/unknown", req.file_size or "48.2 MB")
    forensic_logger.analysis_started(case_id, analysis_id)

    # 1. Create or ensure case record
    existing_case = repo.get_case(case_id)
    if not existing_case:
        repo.create_case(
            case_id=case_id,
            media_id=media_id,
            filename=clean_filename,
            media_type=req.media_type,
            status="PROCESSING"
        )

    # 2. Create analysis record with status = PROCESSING
    repo.create_analysis(analysis_id=analysis_id, case_id=case_id, status="PROCESSING")

    try:
        # 3. Run the existing mock detector adapters (via orchestrator)
        std_result, db_payload = orchestrator.process(
            filename=clean_filename,
            media_type=req.media_type,
            file_size=req.file_size or "48.2 MB",
            case_id=case_id,
            analysis_id=analysis_id
        )

        # 4. Save results to the database
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

        # Save media record
        repo.create_media(
            media_id=std_result.media_id,
            case_id=case_id,
            filename=clean_filename,
            mime_type=std_result.metadata.get("mimeType", "video/mp4"),
            file_size=req.file_size or "48.2 MB",
            sha256=std_result.sha256,
            resolution=std_result.metadata.get("resolution", "1920x1080"),
            duration=std_result.metadata.get("duration", "00:32.4"),
            codec=std_result.metadata.get("codec", "H.264 / AVC"),
            metadata_json=std_result.metadata,
            c2pa_status=std_result.provenance.status
        )

        # 5. Save forensic signals
        repo.add_signals(analysis_id, db_payload["signals"])

        # 6. Save timeline events
        repo.add_timeline_events(analysis_id, db_payload["timeline"])

        # Update case with results
        repo.update_case_results(
            case_id=case_id,
            status="COMPLETE",
            overall_risk=std_result.risk.overall,
            risk_level=std_result.risk.level,
            confidence=std_result.confidence,
            model_consensus=std_result.consensus
        )

        # 7 & 8. Status COMPLETE
        forensic_logger.analysis_completed(case_id, analysis_id, std_result.risk.overall, db_payload["processing_time_ms"])

        ACTIVE_ANALYSES[analysis_id] = {
            "analysis_id": analysis_id,
            "case_id": case_id,
            "created_at": time.time(),
            "status": "PROCESSING",
            "result": std_result.model_dump()
        }

        return AnalysisResponseSchema(
            analysis_id=analysis_id,
            case_id=case_id,
            status="PROCESSING"
        )

    except Exception as exc:
        # Failure handling
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
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "ERR_FORENSIC_ANALYSIS_FAILED",
                "message": f"Forensic analysis pipeline failed: {str(exc)}",
                "case_id": case_id,
                "analysis_id": analysis_id
            }
        )

@router.get("/{analysis_id}")
def get_analysis_status(analysis_id: str, db: Session = Depends(get_db)):
    if analysis_id in ACTIVE_ANALYSES:
        item = ACTIVE_ANALYSES[analysis_id]
        if "result" in item:
            item["status"] = "COMPLETE"
            return item["result"]
        else:
            elapsed = time.time() - item["created_at"]
            return {
                "analysis_id": analysis_id,
                "case_id": item["case_id"],
                "status": "PROCESSING",
                "progress": min(95, int(elapsed * 90))
            }

    # Query persistent database
    repo = ForensicRepository(db)
    rec = repo.get_analysis(analysis_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Analysis ID not found")

    if rec.status == "FAILED":
        return {
            "analysis_id": rec.analysis_id,
            "case_id": rec.case_id,
            "status": "FAILED",
            "error": rec.error_message
        }

    case = repo.get_case(rec.case_id)
    return {
        "analysis_id": rec.analysis_id,
        "case_id": rec.case_id,
        "status": rec.status,
        "overall_score": rec.overall_score,
        "confidence": rec.confidence,
        "visual_score": rec.visual_score,
        "audio_score": rec.audio_score,
        "temporal_score": rec.temporal_score,
        "av_sync_score": rec.av_sync_score
    }

@router.post("/upload", response_model=AnalysisResponseSchema)
async def upload_and_analyze(
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

    existing_case = repo.get_case(case_id_val)
    if not existing_case:
        repo.create_case(
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

            std_result, db_payload = orchestrator.process(
                filename=clean_filename,
                media_type=media_type,
                file_size=media_processor.format_file_size(len(file_bytes)),
                case_id=case_id_val,
                analysis_id=analysis_id,
                file_path=tmp_path
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

        repo.create_media(
            media_id=std_result.media_id,
            case_id=case_id_val,
            filename=clean_filename,
            mime_type=validated_mime,
            file_size=media_processor.format_file_size(len(file_bytes)),
            sha256=std_result.sha256,
            resolution=std_result.metadata.get("resolution", "1920x1080"),
            duration=std_result.metadata.get("duration", "00:30.00"),
            codec=std_result.metadata.get("codec", "H.264 / AVC"),
            metadata_json=std_result.metadata,
            c2pa_status=std_result.provenance.status
        )

        repo.add_signals(analysis_id, db_payload["signals"])
        repo.add_timeline_events(analysis_id, db_payload["timeline"])

        repo.update_case_results(
            case_id=case_id_val,
            status="COMPLETE",
            overall_risk=std_result.risk.overall,
            risk_level=std_result.risk.level,
            confidence=std_result.confidence,
            model_consensus=std_result.consensus
        )

        forensic_logger.analysis_completed(case_id_val, analysis_id, std_result.risk.overall, db_payload["processing_time_ms"])

        ACTIVE_ANALYSES[analysis_id] = {
            "analysis_id": analysis_id,
            "case_id": case_id_val,
            "created_at": time.time(),
            "status": "PROCESSING",
            "result": std_result.model_dump()
        }

        return AnalysisResponseSchema(
            analysis_id=analysis_id,
            case_id=case_id_val,
            status="PROCESSING"
        )

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
        raise HTTPException(status_code=500, detail=f"Forensic upload pipeline failed: {str(exc)}")
