import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db import models

class ForensicRepository:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------------------
    # Cases
    # -------------------------------------------------------------------------
    def create_case(
        self,
        case_id: str,
        media_id: str,
        filename: str,
        media_type: str,
        status: str = "PROCESSING"
    ) -> models.ForensicCase:
        case = models.ForensicCase(
            case_id=case_id,
            media_id=media_id,
            filename=filename,
            media_type=media_type,
            status=status
        )
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return case

    def get_case(self, case_id: str) -> Optional[models.ForensicCase]:
        return self.db.query(models.ForensicCase).filter(
            models.ForensicCase.case_id == case_id
        ).first()

    def list_cases(self, limit: int = 50) -> List[models.ForensicCase]:
        return self.db.query(models.ForensicCase).order_by(
            models.ForensicCase.created_at.desc()
        ).limit(limit).all()

    def update_case_results(
        self,
        case_id: str,
        status: str,
        overall_risk: float,
        risk_level: str,
        confidence: float,
        model_consensus: float
    ) -> Optional[models.ForensicCase]:
        case = self.get_case(case_id)
        if case:
            case.status = status
            case.overall_risk = overall_risk
            case.risk_level = risk_level
            case.confidence = confidence
            case.model_consensus = model_consensus
            if status == "COMPLETE":
                case.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(case)
        return case

    # -------------------------------------------------------------------------
    # Media
    # -------------------------------------------------------------------------
    def create_media(
        self,
        media_id: str,
        case_id: str,
        filename: str,
        mime_type: str,
        file_size: str,
        sha256: str,
        resolution: Optional[str] = None,
        duration: Optional[str] = None,
        codec: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
        c2pa_status: str = "UNVERIFIED"
    ) -> models.MediaItem:
        media = models.MediaItem(
            media_id=media_id,
            case_id=case_id,
            filename=filename,
            mime_type=mime_type,
            file_size=file_size,
            sha256=sha256,
            resolution=resolution,
            duration=duration,
            codec=codec,
            metadata_json=json.dumps(metadata_json or {}),
            c2pa_status=c2pa_status
        )
        self.db.add(media)
        self.db.commit()
        self.db.refresh(media)
        return media

    def get_media_by_case(self, case_id: str) -> Optional[models.MediaItem]:
        return self.db.query(models.MediaItem).filter(
            models.MediaItem.case_id == case_id
        ).first()

    # -------------------------------------------------------------------------
    # Analyses
    # -------------------------------------------------------------------------
    def create_analysis(
        self,
        analysis_id: str,
        case_id: str,
        status: str = "PROCESSING"
    ) -> models.AnalysisRecord:
        analysis = models.AnalysisRecord(
            analysis_id=analysis_id,
            case_id=case_id,
            status=status
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def get_analysis(self, analysis_id: str) -> Optional[models.AnalysisRecord]:
        return self.db.query(models.AnalysisRecord).filter(
            models.AnalysisRecord.analysis_id == analysis_id
        ).first()

    def get_analysis_by_case(self, case_id: str) -> Optional[models.AnalysisRecord]:
        return self.db.query(models.AnalysisRecord).filter(
            models.AnalysisRecord.case_id == case_id
        ).order_by(models.AnalysisRecord.created_at.desc()).first()

    def complete_analysis(
        self,
        analysis_id: str,
        visual_score: float,
        audio_score: float,
        temporal_score: float,
        av_sync_score: float,
        overall_score: float,
        confidence: float,
        consensus: float,
        processing_time_ms: int,
        model_versions: Dict[str, str]
    ) -> Optional[models.AnalysisRecord]:
        rec = self.get_analysis(analysis_id)
        if rec:
            rec.status = "COMPLETE"
            rec.visual_score = visual_score
            rec.audio_score = audio_score
            rec.temporal_score = temporal_score
            rec.av_sync_score = av_sync_score
            rec.overall_score = overall_score
            rec.confidence = confidence
            rec.consensus = consensus
            rec.processing_time_ms = processing_time_ms
            rec.model_versions = json.dumps(model_versions)
            rec.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(rec)
        return rec

    def fail_analysis(self, analysis_id: str, error_message: str) -> Optional[models.AnalysisRecord]:
        rec = self.get_analysis(analysis_id)
        if rec:
            rec.status = "FAILED"
            rec.error_message = error_message
            rec.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(rec)
        return rec

    # -------------------------------------------------------------------------
    # Signals
    # -------------------------------------------------------------------------
    def add_signals(self, analysis_id: str, signals_data: List[Dict[str, Any]]):
        signals = []
        for s in signals_data:
            sig = models.ForensicSignal(
                analysis_id=analysis_id,
                signal_name=s.get("name") or s.get("signal_name", "Anomaly Detected"),
                category=s.get("category", "visual"),
                severity=s.get("severity", "medium"),
                confidence=float(s.get("confidence", 85.0)),
                region=s.get("affectedRegionOrTime") or s.get("region"),
                timestamp=s.get("affectedRegionOrTime") or s.get("timestamp"),
                technical_rationale=s.get("explanation") or s.get("technical_rationale")
            )
            signals.append(sig)
        if signals:
            self.db.add_all(signals)
            self.db.commit()

    def get_signals_by_analysis(self, analysis_id: str) -> List[models.ForensicSignal]:
        return self.db.query(models.ForensicSignal).filter(
            models.ForensicSignal.analysis_id == analysis_id
        ).all()

    # -------------------------------------------------------------------------
    # Timeline Events
    # -------------------------------------------------------------------------
    def add_timeline_events(self, analysis_id: str, events_data: List[Dict[str, Any]]):
        events = []
        for ev in events_data:
            t_event = models.TimelineEvent(
                analysis_id=analysis_id,
                timestamp=float(ev.get("timestampSec", 0.0)),
                frame_number=int(ev.get("frameNumber", 1)),
                visual_score=float(ev.get("visualScore", 0.0)),
                audio_score=float(ev.get("audioScore", 0.0)),
                av_sync_score=float(ev.get("avSyncScore", 0.0)),
                severity=ev.get("severity", "LOW"),
                description=ev.get("explanation") or ev.get("description", "")
            )
            events.append(t_event)
        if events:
            self.db.add_all(events)
            self.db.commit()

    def get_timeline_by_analysis(self, analysis_id: str) -> List[models.TimelineEvent]:
        return self.db.query(models.TimelineEvent).filter(
            models.TimelineEvent.analysis_id == analysis_id
        ).order_by(models.TimelineEvent.timestamp.asc()).all()

    # -------------------------------------------------------------------------
    # Model Registry
    # -------------------------------------------------------------------------
    def get_model_registry(self) -> List[models.ModelRegistry]:
        return self.db.query(models.ModelRegistry).all()
