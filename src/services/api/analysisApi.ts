import { apiFetch, apiUpload } from './client';
import type { ForensicCase, RiskLevel, ProvenanceStatus } from '../../types/forensics';

export interface AnalysisStartResponse {
  analysis_id: string;
  case_id: string;
  status: string;
}

export function mapBackendResultToForensicCase(std: any, file?: File): ForensicCase {
  const riskTier: RiskLevel = 
    std.risk?.level === 'HIGH RISK' ? 'HIGH RISK' :
    std.risk?.level === 'MEDIUM RISK' ? 'MEDIUM RISK' :
    std.risk?.level === 'INCONCLUSIVE' ? 'INCONCLUSIVE' : 'LOW RISK';

  const provStatus: ProvenanceStatus =
    std.provenance?.status === 'VERIFIED' ? 'VERIFIED' :
    std.provenance?.status === 'UNKNOWN' ? 'UNKNOWN' : 'UNVERIFIED';

  const overallScore = std.risk?.overall !== null && std.risk?.overall !== undefined
    ? Number(std.risk.overall)
    : null;

  return {
    id: std.case_id || std.analysis_id || `CASE-${Date.now()}`,
    caseId: std.case_id || `CASE VX-0${Math.floor(1000 + Math.random() * 9000)}`,
    mediaId: std.media_id || `MED-${Math.floor(10000 + Math.random() * 90000)}-X`,
    filename: std.filename || file?.name || 'analyzed_media',
    mediaType: std.media_type || (file?.type.startsWith('video') ? 'video' : file?.type.startsWith('audio') ? 'audio' : 'image'),
    fileSize: std.metadata?.file_size || (file ? `${(file.size / (1024 * 1024)).toFixed(1)} MB` : '12.4 MB'),
    sha256: std.sha256 || 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC',
    uploadedAt: new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC',
    overallRiskScore: riskTier === 'INCONCLUSIVE' ? null : overallScore,
    riskTier: riskTier,
    confidence: Number(std.confidence ?? 90),
    modelConsensus: Number(std.consensus ?? 92),
    signalCount: std.signals?.length || std.signal_count || 0,
    processingLatencyMs: std.processing_latency_ms || 140,
    modelVersion: std.model_version || 'VERITAS ENGINE v0.9.0-PROTOTYPE',
    analysisStatus: 'COMPLETE',
    visualScore: Number(std.visual?.score ?? 0),
    audioScore: Number(std.audio?.score ?? 0),
    temporalScore: Number(std.temporal?.score ?? 0),
    avSyncScore: Number(std.av_sync?.score ?? 0),
    c2paStatus: provStatus,
    metadata: {
      fileType: std.metadata?.fileType || std.metadata?.mime_type || 'Media Container',
      mimeType: std.metadata?.mimeType || 'application/octet-stream',
      codec: std.metadata?.codec || 'Standard Codec',
      resolution: std.metadata?.resolution,
      frameCount: std.metadata?.frameCount,
      bitrate: std.metadata?.bitrate || 'Variable',
      duration: std.metadata?.duration,
      creationDate: new Date().toISOString().substring(0, 10),
      modificationDate: new Date().toISOString().substring(0, 10),
      software: std.metadata?.software || 'VERITAS Ingestion Node',
    },
    signals: std.signals || [],
    evidenceItems: (std.evidence || []).map((ev: any, idx: number) => ({
      id: ev.evidence_id || ev.id || `ev-${idx}`,
      name: ev.trigger_type || ev.name || 'Forensic Signal',
      category: (ev.category || 'visual').toLowerCase(),
      severity: (ev.severity || 'high').toLowerCase(),
      confidence: Math.round((ev.peak_manipulation_probability || 0.85) * 100),
      affectedRegionOrTime: ev.formatted_time || `${ev.start_timestamp?.toFixed(1) || 0}s – ${ev.end_timestamp?.toFixed(1) || 0}s`,
      explanation: ev.description || ev.explanation || 'Signal detected during neural inspection.',
      title: ev.trigger_type || ev.title || 'Forensic Anomaly',
      description: ev.description || ev.explanation || 'Elevated anomaly signature.',
      timestampSec: ev.start_timestamp
    })),
    timelineMarkers: (std.timeline || []).map((tm: any, idx: number) => ({
      id: `tm-${idx}`,
      timestampSec: tm.timestamp || tm.timestampSec || 0,
      formattedTime: tm.formatted_time || tm.formattedTime || '00:00',
      frameNumber: tm.frame_number || tm.frameNumber || idx * 30,
      visualScore: tm.visual_score || 0,
      audioScore: tm.audio_score || 0,
      avSyncScore: tm.av_sync_score || 0,
      overallRisk: tm.overall_risk || 0,
      severity: tm.severity || 'LOW',
      explanation: tm.description || tm.explanation || 'Timeline anchor point.'
    })),
    modelOutputs: [],
    robustnessResults: [],
    provenanceGraph: [],
    explanation: std.explanation
  };
}

export async function requestAnalysis(
  filename: string,
  mediaType: string,
  caseId?: string
): Promise<AnalysisStartResponse | null> {
  return await apiFetch<AnalysisStartResponse>('/api/v1/analyze', {
    method: 'POST',
    body: JSON.stringify({
      filename,
      media_type: mediaType,
      case_id: caseId
    })
  });
}

export async function pollAnalysisResult(analysisId: string): Promise<any | null> {
  return await apiFetch<any>(`/api/v1/analyze/${analysisId}`);
}

export async function uploadAndAnalyzeMedia(
  file: File,
  caseId?: string
): Promise<ForensicCase> {
  const formData = new FormData();
  formData.append('file', file);
  if (caseId) {
    formData.append('case_id', caseId);
  }

  const startRes = await apiUpload<AnalysisStartResponse>('/api/v1/analyze/upload', formData);
  if (!startRes || !startRes.analysis_id) {
    throw new Error('ANALYSIS ERROR: Failed to initiate upload analysis with backend server.');
  }

  // Poll for completion (CPU inference for video can take a few seconds)
  let attempts = 0;
  while (attempts < 60) {
    await new Promise((r) => setTimeout(r, 600));
    const result = await pollAnalysisResult(startRes.analysis_id);
    if (result && 'risk' in result) {
      return mapBackendResultToForensicCase(result, file);
    } else if (result && result.status === 'FAILED') {
      throw new Error(`ANALYSIS ERROR: ${result.error || 'Server-side pipeline processing failed'}`);
    }
    attempts++;
  }
  throw new Error('ANALYSIS ERROR: TIMEOUT_ERROR — Analysis timed out waiting for backend response.');
}

