"""
VERITAS AI — Forensic Explanation Engine Test Suite
Module: backend.tests.test_explanation_engine

Verifies truthfulness, safety rules, evidence derivation, and cross-modal reasoning
in human-auditable forensic explanations.
"""

import sys
import unittest
from pathlib import Path

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.services.explanation_engine import explanation_engine, ForensicExplanationEngine


class TestForensicExplanationEngine(unittest.TestCase):
    """Test suite covering the 6 key explanation generation rules."""

    def test_high_risk_explanation(self):
        exp = explanation_engine.generate_explanation(
            overall_score=82,
            risk_level="HIGH RISK",
            confidence=91,
            media_type="video",
            modality_results={
                "visual": {"score": 85, "signals": []},
                "temporal": {"score": 75, "signals": []}
            },
            evidence_windows=[
                {
                    "evidence_id": "EV-001",
                    "trigger_type": "FACIAL_MANIPULATION_SPIKE",
                    "start_timestamp": 7.0,
                    "end_timestamp": 10.0,
                    "peak_manipulation_probability": 0.88
                }
            ],
            provenance_status="UNVERIFIED"
        )
        self.assertEqual(exp.risk_level, "HIGH RISK")
        self.assertIn("SYNTHETIC MANIPULATION RISK", exp.headline)
        self.assertGreaterEqual(len(exp.reasons), 2)
        categories = [r["category"] for r in exp.reasons]
        self.assertIn("VISUAL", categories)
        self.assertIn("PROVENANCE", categories)

    def test_low_risk_organic_explanation(self):
        exp = explanation_engine.generate_explanation(
            overall_score=15,
            risk_level="LOW RISK",
            confidence=93,
            media_type="video",
            modality_results={
                "visual": {"score": 12, "signals": []},
                "temporal": {"score": 10, "signals": []}
            },
            provenance_status="VALID"
        )
        self.assertEqual(exp.risk_level, "LOW RISK")
        self.assertIn("AUTHENTIC", exp.headline)
        self.assertIn("organic", exp.summary.lower())

    def test_inconclusive_zero_face_explanation(self):
        exp = explanation_engine.generate_explanation(
            overall_score=0,
            risk_level="INCONCLUSIVE",
            confidence=0,
            media_type="video",
            classification_status="INSUFFICIENT_FACE_EVIDENCE"
        )
        self.assertEqual(exp.risk_level, "INCONCLUSIVE")
        self.assertIn("INSUFFICIENT FORENSIC EVIDENCE", exp.headline)
        self.assertIn("could not obtain sufficient", exp.summary)

    def test_disagreement_explanation(self):
        exp = explanation_engine.generate_explanation(
            overall_score=50,
            risk_level="INCONCLUSIVE",
            confidence=55,
            media_type="video",
            modality_results={
                "visual": {"score": 85, "signals": []},
                "temporal": {"score": 10, "signals": []}
            },
            disagreement_detected=True,
            disagreement_score=38
        )
        self.assertIn("DISAGREEMENT", exp.headline)
        categories = [r["category"] for r in exp.reasons]
        self.assertIn("CONSENSUS", categories)

    def test_audio_evidence_explanation(self):
        exp = explanation_engine.generate_explanation(
            overall_score=75,
            risk_level="HIGH RISK",
            confidence=88,
            media_type="audio",
            modality_results={
                "audio": {
                    "score": 78,
                    "segments": [
                        {
                            "segment_id": "seg-1",
                            "start_timestamp": 8.0,
                            "end_timestamp": 12.0,
                            "spoof_probability": 0.82
                        }
                    ]
                }
            }
        )
        categories = [r["category"] for r in exp.reasons]
        self.assertIn("AUDIO", categories)
        audio_reason = next(r for r in exp.reasons if r["category"] == "AUDIO")
        self.assertIn("RawNet2", audio_reason["description"])
        self.assertEqual(audio_reason["timestamp_start"], 8.0)
        self.assertEqual(audio_reason["timestamp_end"], 12.0)

    def test_provenance_absence_safety_rule(self):
        exp = explanation_engine.generate_explanation(
            overall_score=30,
            risk_level="LOW RISK",
            confidence=85,
            media_type="image",
            provenance_status="UNVERIFIED"
        )
        prov_reason = next(r for r in exp.reasons if r["category"] == "PROVENANCE")
        # Ensure it does NOT claim media is fake because provenance is missing
        self.assertNotIn("fake because", prov_reason["description"].lower())
        self.assertIn("not affirmative manipulation", prov_reason["description"].lower())


if __name__ == "__main__":
    unittest.main()
