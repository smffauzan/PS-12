from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class RiskBreakdown(BaseModel):
    overall: Optional[int] = Field(None, json_schema_extra={"example": 87})
    level: str = Field(..., json_schema_extra={"example": "HIGH RISK"})

class ForensicSignalSchema(BaseModel):
    id: str
    name: str
    category: str
    severity: str
    confidence: int
    affectedRegionOrTime: str
    explanation: str

class ModalityScore(BaseModel):
    score: int
    signals: List[ForensicSignalSchema] = []

class ProvenanceResult(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "UNVERIFIED"})

class AnalysisRequestSchema(BaseModel):
    case_id: Optional[str] = None
    filename: str
    media_type: str
    file_size: Optional[str] = "48.2 MB"

class AnalysisResponseSchema(BaseModel):
    analysis_id: str
    case_id: str
    status: str

class StandardizedForensicResult(BaseModel):
    analysis_id: str
    case_id: str
    media_id: str
    filename: str
    media_type: str
    status: str
    sha256: str
    risk: RiskBreakdown
    confidence: int
    consensus: int
    signal_count: int
    processing_latency_ms: int
    model_version: str = "VERITAS ENGINE v0.9.0-PROTOTYPE"
    visual: ModalityScore
    audio: ModalityScore
    temporal: ModalityScore
    av_sync: ModalityScore
    provenance: ProvenanceResult
    timeline: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []
    signals: List[ForensicSignalSchema] = []
    metadata: Dict[str, Any] = {}
    provenance_graph: List[Dict[str, Any]] = []
    robustness_results: List[Dict[str, Any]] = []
    explanation: Optional[Dict[str, Any]] = None
