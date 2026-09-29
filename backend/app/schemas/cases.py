from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class CaseCreateSchema(BaseModel):
    filename: str
    media_type: str
    file_size: Optional[str] = "48.2 MB"
    case_id: Optional[str] = None

class CaseSummarySchema(BaseModel):
    case_id: str
    media_id: str
    filename: str
    media_type: str
    risk_score: int
    risk_tier: str
    confidence: int
    consensus: int
    signal_count: int
    timestamp: str
    status: str

class CaseListResponse(BaseModel):
    cases: List[CaseSummarySchema]
    total: int
