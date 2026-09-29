import type { ForensicCase, ForensicExplanation, ExplanationReason } from '../types/forensics';

/**
 * VERITAS AI — Client-Side Forensic Explanation Engine
 * 
 * Derives dynamic, evidence-grounded, human-interpretable forensic explanations
 * strictly from actual analysis results, evidence windows, and forensic signals.
 * Strictly media-aware: never presents visual claims for audio-only, or audio claims for images.
 * Never hallucinates forensic claims or unobserved signals.
 */
export function generateForensicExplanation(item: ForensicCase): ForensicExplanation {
  const reasons: ExplanationReason[] = [];
  const score = item.overallRiskScore;
  const isVideo = item.mediaType === 'video';
  const isAudio = item.mediaType === 'audio';
  const isImage = item.mediaType === 'image';

  // If backend provided an explanation, filter its reasons to match active mediaType
  if (item.explanation && item.explanation.reasons && item.explanation.reasons.length > 0) {
    const validReasons = item.explanation.reasons.filter(r => {
      if (isImage && (r.category === 'AUDIO' || r.category === 'A/V SYNC' || r.category === 'TEMPORAL')) return false;
      if (isAudio && (r.category === 'VISUAL' || r.category === 'A/V SYNC' || r.category === 'TEMPORAL')) return false;
      return true;
    });

    return {
      ...item.explanation,
      reasons: validReasons
    };
  }

  // 1. Headline & Summary determination
  let headline = 'AUTHENTIC MEDIA CHARACTERISTICS OBSERVED';
  let summary = 'Analysis across visual, temporal, and acoustic domains indicates organic, unaltered media characteristics.';

  if (item.riskTier === 'INCONCLUSIVE' || item.analysisStatus === 'QUEUED') {
    headline = 'INSUFFICIENT FORENSIC EVIDENCE';
    if (isImage) {
      summary = 'Insufficient facial evidence was available for visual deepfake classification.';
    } else if (isAudio) {
      summary = 'Insufficient audio evidence was available for reliable speech anti-spoofing analysis.';
    } else {
      summary = 'The available evidence is insufficient to determine manipulation risk reliably.';
    }
  } else if ((score !== null && score >= 80) || item.riskTier === 'HIGH RISK') {
    headline = 'HIGH MANIPULATION RISK';
    summary = 'Multiple forensic signals indicate elevated risk of AI-generated or manipulated media.';
  } else if ((score !== null && score >= 45) || item.riskTier === 'MEDIUM RISK') {
    headline = 'MEDIUM MANIPULATION RISK';
    summary = 'Some forensic signals indicate possible synthetic or manipulated media.';
  } else {
    headline = 'LOW MANIPULATION RISK';
    summary = 'No strong synthetic-media signals were detected by the available analysis.';
  }

  // 2. VISUAL EVIDENCE (Images & Videos only)
  if (!isAudio) {
    const visualEv = item.evidenceItems.find(e => e.category === 'visual');
    if (item.riskTier === 'INCONCLUSIVE' && isImage) {
      reasons.push({
        category: 'VISUAL',
        title: 'Insufficient Forensic Evidence',
        description: 'The available visual and frequency evidence was insufficient for definitive classification.',
        severity: 'LOW',
        evidence_ids: ['INSUFFICIENT_EVIDENCE']
      });
    } else if (visualEv) {
      reasons.push({
        category: 'VISUAL',
        title: visualEv.title || 'Visual Forensic Analysis',
        description: visualEv.description || 'Elevated spatial texture or generative anomalies were detected.',
        timestamp_start: visualEv.timestampSec ? Math.max(0, visualEv.timestampSec - 2) : undefined,
        timestamp_end: visualEv.timestampSec ? visualEv.timestampSec + 2 : undefined,
        severity: visualEv.severity === 'high' ? 'HIGH' : visualEv.severity === 'medium' ? 'MEDIUM' : 'LOW',
        evidence_ids: [visualEv.id || 'EV-VIS-01']
      });
    } else if (item.visualScore >= 50) {
      reasons.push({
        category: 'VISUAL',
        title: 'Visual Forensic Analysis',
        description: `Elevated spatial texture or generative anomalies detected (${item.visualScore}% risk).`,
        severity: item.visualScore >= 75 ? 'HIGH' : 'MEDIUM',
        evidence_ids: ['SIG-VIS-SCORE']
      });
    }
  }

  // 3. TEMPORAL EVIDENCE (Videos only)
  if (isVideo) {
    const temporalEv = item.evidenceItems.find(e => e.category === 'temporal');
    if (temporalEv) {
      reasons.push({
        category: 'TEMPORAL',
        title: temporalEv.title || 'Temporal Continuity Analysis',
        description: temporalEv.description || 'Abnormal variation was detected across consecutive video frames.',
        timestamp_start: temporalEv.timestampSec ? Math.max(0, temporalEv.timestampSec - 1.5) : undefined,
        timestamp_end: temporalEv.timestampSec ? temporalEv.timestampSec + 1.5 : undefined,
        severity: temporalEv.severity === 'high' ? 'HIGH' : 'MEDIUM',
        evidence_ids: [temporalEv.id || 'EV-TMP-01']
      });
    } else if (item.temporalScore >= 55) {
      reasons.push({
        category: 'TEMPORAL',
        title: 'Temporal Continuity Analysis',
        description: `Abnormal variation was detected across consecutive video frames (${item.temporalScore}% risk).`,
        severity: item.temporalScore >= 75 ? 'HIGH' : 'MEDIUM',
        evidence_ids: ['SIG-TMP-JITTER']
      });
    }
  }

  // 4. AUDIO EVIDENCE (Audio & Videos only)
  if (!isImage) {
    const audioEv = item.evidenceItems.find(e => e.category === 'audio');
    if (item.riskTier === 'INCONCLUSIVE' && isAudio) {
      reasons.push({
        category: 'AUDIO',
        title: 'Insufficient Audio Evidence',
        description: 'Insufficient audio duration or speech energy was available for anti-spoofing verification.',
        severity: 'LOW',
        evidence_ids: ['INSUFFICIENT_AUDIO']
      });
    } else if (audioEv) {
      reasons.push({
        category: 'AUDIO',
        title: audioEv.title || 'Audio Anti-Spoofing Analysis',
        description: audioEv.description || 'Speech anti-spoofing analysis detected elevated synthetic-speech signals.',
        timestamp_start: audioEv.timestampSec ? Math.max(0, audioEv.timestampSec - 2) : undefined,
        timestamp_end: audioEv.timestampSec ? audioEv.timestampSec + 2 : undefined,
        severity: audioEv.severity === 'high' ? 'HIGH' : 'MEDIUM',
        evidence_ids: [audioEv.id || 'EV-AUD-01']
      });
    } else if (item.audioScore >= 60) {
      reasons.push({
        category: 'AUDIO',
        title: 'Audio Anti-Spoofing Analysis',
        description: `Speech anti-spoofing analysis detected elevated synthetic-speech signals (${item.audioScore}% risk).`,
        severity: item.audioScore >= 75 ? 'HIGH' : 'MEDIUM',
        evidence_ids: ['SIG-AUD-SCORE']
      });
    } else if (isVideo && item.audioScore === 0) {
      reasons.push({
        category: 'AUDIO',
        title: 'Audio Track Inspection',
        description: 'Audio analysis was unavailable because no usable speech track was detected.',
        severity: 'LOW',
        evidence_ids: ['NO_AUDIO_TRACK']
      });
    }
  }

  // 5. A/V SYNC EVIDENCE (Videos with audio only)
  if (isVideo && item.audioScore > 0) {
    const syncEv = item.evidenceItems.find(e => e.category === 'sync');
    if (syncEv) {
      reasons.push({
        category: 'A/V SYNC',
        title: syncEv.title || 'Audio-Visual Synchronization',
        description: syncEv.description || 'Phoneme-viseme temporal alignment detected plosive phase delay between speech audio and visual labial contact.',
        timestamp_start: syncEv.timestampSec,
        timestamp_end: syncEv.timestampSec ? syncEv.timestampSec + 1 : undefined,
        severity: 'HIGH',
        evidence_ids: [syncEv.id || 'EV-SYNC-01']
      });
    } else if (item.avSyncScore >= 70) {
      reasons.push({
        category: 'A/V SYNC',
        title: 'Audio-Visual Synchronization',
        description: 'Phoneme-viseme temporal alignment detected significant phase delay between speech audio and lip movement.',
        severity: 'HIGH',
        evidence_ids: ['SIG-SYNC-SCORE']
      });
    }
  }

  // 6. PROVENANCE (Strict Rule: Absence of provenance != fake)
  if (item.c2paStatus === 'UNVERIFIED' || item.c2paStatus === 'UNKNOWN') {
    reasons.push({
      category: 'PROVENANCE',
      title: 'Provenance Verification',
      description: 'No verifiable provenance information was found. (Note: Lack of provenance indicates untracked lineage, not affirmative manipulation).',
      severity: 'LOW',
      evidence_ids: ['PROV-UNVERIFIED']
    });
  } else if (item.c2paStatus === 'VERIFIED') {
    reasons.push({
      category: 'PROVENANCE',
      title: 'Provenance Verification',
      description: 'Cryptographic C2PA manifest confirms verified hardware capture origin and unaltered chain-of-custody.',
      severity: 'LOW',
      evidence_ids: ['PROV-VERIFIED']
    });
  }

  // 7. MODEL CONSENSUS & DISAGREEMENT
  const relevantScores = (isImage ? [item.visualScore] : isAudio ? [item.audioScore] : [item.visualScore, item.audioScore, item.temporalScore]).filter(s => s > 0);
  if (relevantScores.length >= 2) {
    const maxScore = Math.max(...relevantScores);
    const minScore = Math.min(...relevantScores);
    if (maxScore - minScore >= 40) {
      headline = 'CROSS-MODAL EVIDENCE INCONCLUSIVE / DISAGREEMENT';
      summary = 'Evidence is mixed across analysis methods. Individual modality detectors report conflicting indicators requiring human review.';
      reasons.push({
        category: 'CONSENSUS',
        title: 'Cross-Modal Evidence Divergence',
        description: `Individual modality detectors produced divergent results. A human analyst must review modality-specific signals.`,
        severity: 'MEDIUM',
        evidence_ids: ['ENS-DISAGREEMENT']
      });
    }
  }

  // 8. Limitations & Disclosures
  const limitations = [
    'calibration_status = NOT_CALIBRATED (raw scores represent neural classification activations, not calibrated Bayesian probabilities)',
    'Absence of cryptographic provenance indicates untracked lineage, not affirmative manipulation',
    'Algorithmic forensic scores should be corroborated with investigative context before final attribution'
  ];

  return {
    headline,
    summary,
    overall_risk_score: item.overallRiskScore,
    risk_level: item.riskTier,
    confidence: item.confidence,
    calibration_status: 'NOT_CALIBRATED',
    reasons,
    limitations
  };
}

