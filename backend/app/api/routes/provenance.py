from fastapi import APIRouter
from pydantic import BaseModel
from app.services.provenance_service import ProvenanceService

router = APIRouter(prefix="/provenance", tags=["Provenance"])
prov_service = ProvenanceService()

class ProvenanceCheckRequest(BaseModel):
    sha256: str

@router.post("/check")
def check_provenance(req: ProvenanceCheckRequest):
    return prov_service.check_manifest(req.sha256)
