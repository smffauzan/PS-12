import logging
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# Configure standard logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [VERITAS-FORENSICS] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("veritas.forensics")

class ForensicStructuredLogger:
    @staticmethod
    def _emit(event_type: str, data: Dict[str, Any]):
        payload = {
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data
        }
        logger.info(json.dumps(payload))

    @classmethod
    def case_created(cls, case_id: str, media_id: str, filename: str):
        cls._emit("CASE_CREATED", {
            "case_id": case_id,
            "media_id": media_id,
            "filename": filename
        })

    @classmethod
    def media_received(cls, case_id: str, media_id: str, filename: str, mime_type: str, size: str):
        cls._emit("MEDIA_RECEIVED", {
            "case_id": case_id,
            "media_id": media_id,
            "filename": filename,
            "mime_type": mime_type,
            "file_size": size
        })

    @classmethod
    def analysis_started(cls, case_id: str, analysis_id: str):
        cls._emit("ANALYSIS_STARTED", {
            "case_id": case_id,
            "analysis_id": analysis_id
        })

    @classmethod
    def model_started(cls, case_id: str, analysis_id: str, model_name: str, modality: str):
        cls._emit("MODEL_STARTED", {
            "case_id": case_id,
            "analysis_id": analysis_id,
            "model_name": model_name,
            "modality": modality
        })

    @classmethod
    def model_completed(cls, case_id: str, analysis_id: str, model_name: str, processing_time_ms: float, score: float):
        cls._emit("MODEL_COMPLETED", {
            "case_id": case_id,
            "analysis_id": analysis_id,
            "model_name": model_name,
            "processing_time_ms": processing_time_ms,
            "score": score
        })

    @classmethod
    def analysis_completed(cls, case_id: str, analysis_id: str, overall_risk: float, processing_time_ms: float):
        cls._emit("ANALYSIS_COMPLETED", {
            "case_id": case_id,
            "analysis_id": analysis_id,
            "overall_risk": overall_risk,
            "processing_time_ms": processing_time_ms
        })

    @classmethod
    def analysis_failed(cls, case_id: str, analysis_id: str, error_message: str, processing_time_ms: Optional[float] = None):
        cls._emit("ANALYSIS_FAILED", {
            "case_id": case_id,
            "analysis_id": analysis_id,
            "error_message": error_message,
            "processing_time_ms": processing_time_ms or 0
        })

forensic_logger = ForensicStructuredLogger()
