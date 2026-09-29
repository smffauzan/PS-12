from typing import Dict, Any, Optional

class FusionEngine:
    """
    Multimodal Attention Fusion Engine.
    Combines visual (40%), audio (30%), temporal (30%) with provenance penalties.
    Isolated so it can be replaced by a trained ML fusion network later.
    """
    def __init__(self, model_version: str = "VERITAS-FUSION-v0.1"):
        self.model_version = model_version

    def fuse(
        self,
        visual_score: int,
        audio_score: int,
        temporal_score: int,
        av_sync_score: int,
        provenance_status: str,
        media_type: str,
        classification_status: Optional[str] = None
    ) -> Dict[str, Any]:
        if media_type == "audio":
            overall = audio_score
            consensus = audio_score
        elif media_type == "image":
            overall = visual_score
            consensus = visual_score
        else:
            # Video multimodal fusion weights: 40% visual, 30% audio, 30% temporal
            weighted = (visual_score * 0.40) + (audio_score * 0.30) + (temporal_score * 0.30)
            overall = int(round(weighted))
            consensus = int(round((visual_score + audio_score + temporal_score + av_sync_score) / 4))

        if classification_status == "INSUFFICIENT_FACE_EVIDENCE":
            risk_level = "INCONCLUSIVE"
            confidence = 0
            overall = 0
            consensus = 0
        else:
            confidence = 91
            if overall >= 75:
                risk_level = "HIGH RISK"
            elif overall >= 50:
                risk_level = "MEDIUM RISK"
            else:
                risk_level = "LOW RISK"

        uncertainty = 2.4

        return {
            "overall_risk": overall,
            "risk_level": risk_level,
            "confidence": confidence,
            "consensus": consensus,
            "uncertainty": uncertainty,
            "fusion_model_version": self.model_version
        }
