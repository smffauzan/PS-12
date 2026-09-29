from abc import ABC, abstractmethod
from typing import Dict, Any

class AVSyncDetector(ABC):
    """Abstract base detector interface for audio-visual phoneme-viseme coherence."""
    
    @abstractmethod
    def analyze(self, media_path_or_bytes: Any) -> Dict[str, Any]:
        pass

class MockAVSyncDetector(AVSyncDetector):
    def __init__(self, model_version: str = "VERITAS-AVSYNC-v0.1"):
        self.model_version = model_version

    def analyze(self, media_path_or_bytes: Any) -> Dict[str, Any]:
        return {
            "model_name": "A/V Sync Phoneme Alignment Transformer",
            "model_version": self.model_version,
            "category": "Multi-Model",
            "score": 81,
            "confidence": 91,
            "signals": [
                {
                    "id": "sig-sync-1",
                    "name": "Lip-Sync Phase Deviation (+45ms)",
                    "category": "sync",
                    "severity": "high",
                    "confidence": 88,
                    "affectedRegionOrTime": "Plosive Phoneme /p/ [00:18.20]",
                    "explanation": "Acoustic plosive energy precedes visual labial occlusion frames by 45ms."
                }
            ],
            "latency_ms": 22
        }
