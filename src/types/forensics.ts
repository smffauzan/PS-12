export type MediaType = 'image' | 'video' | 'audio';
export type RiskLevel = 'LOW RISK' | 'MEDIUM RISK' | 'HIGH RISK' | 'INCONCLUSIVE';
export type ProvenanceStatus = 'VERIFIED' | 'UNVERIFIED' | 'UNKNOWN';
export type AnalysisStageStatus = 'QUEUED' | 'PROCESSING' | 'COMPLETE';

export interface MetadataDetails {
  fileType: string;
  mimeType: string;
  codec: string;
  resolution?: string;
  frameCount?: number;
  bitrate: string;
  duration?: string;
  creationDate: string;
  modificationDate: string;
  software: string;
  colorSpace?: string;
  sampleRate?: string;
  channels?: string;
  cameraModel?: string;
  gpsData?: string;
}

export interface ForensicSignal {
  id: string;
  name: string;
  category: 'visual' | 'audio' | 'temporal' | 'metadata' | 'sync';
  severity: 'high' | 'medium' | 'low';
  confidence: number;
  affectedRegionOrTime: string;
  explanation: string;
  regionCoords?: { x: number; y: number; width: number; height: number };
}

export interface EvidenceItem extends ForensicSignal {
  timestampSec?: number;
  formattedTime?: string;
  frameNumber?: number;
  location?: string;
  title: string;
  description: string;
}

export interface PipelineStageState {
  id: string;
  name: string;
  status: AnalysisStageStatus;
  timestamp?: string;
  details?: string;
}

export interface TimelineMarker {
  id: string;
  timestampSec: number;
  formattedTime: string;
  frameNumber: number;
  visualScore: number;
  audioScore: number;
  avSyncScore: number;
  overallRisk: number;
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  explanation: string;
  thumbnailUrl?: string;
}

export interface ModelOutput {
  id: string;
  name: string;
  category: 'Visual AI' | 'Audio AI' | 'Temporal AI' | 'Provenance' | 'Multi-Model';
  riskScore: number;
  confidence: number;
  status: 'High Anomaly' | 'Moderate Anomaly' | 'Normal' | 'Unverified';
  description: string;
  latencyMs: number;
}

export interface RobustnessTestResult {
  id: string;
  transformation: string;
  parameter: string;
  originalScore: number;
  transformedScore: number;
  resilienceScore: number;
  status: 'Stable' | 'Slight Degradation' | 'Degraded';
}

export interface ProvenanceNode {
  id: string;
  title: string;
  type: 'source' | 'creation' | 'edit' | 'export' | 'compression' | 'current';
  status: ProvenanceStatus;
  deviceOrSoftware: string;
  timestamp: string;
  details: string;
  c2paCert?: string;
}

export interface ExplanationReason {
  category: 'VISUAL' | 'TEMPORAL' | 'AUDIO' | 'A/V SYNC' | 'PROVENANCE' | 'CONSENSUS';
  title: string;
  description: string;
  timestamp_start?: number;
  timestamp_end?: number;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  evidence_ids: string[];
}

export interface ForensicExplanation {
  headline: string;
  summary: string;
  overall_risk_score: number | null;
  risk_level: string;
  confidence: number;
  calibration_status: string;
  reasons: ExplanationReason[];
  limitations: string[];
}

export interface ForensicCase {
  id: string;
  caseId: string; // e.g. CASE VX-04291
  mediaId: string;
  filename: string;
  mediaType: MediaType;
  fileSize: string;
  sha256: string;
  timestamp: string;
  uploadedAt: string;
  overallRiskScore: number | null;
  riskTier: RiskLevel;
  confidence: number;
  modelConsensus: number;
  signalCount: number;
  processingLatencyMs: number;
  modelVersion: string;
  analysisStatus: 'QUEUED' | 'PROCESSING' | 'COMPLETE';
  
  // Modality Breakdown
  visualScore: number;
  audioScore: number;
  temporalScore: number;
  avSyncScore: number;
  
  // Details & Signals
  metadata: MetadataDetails;
  c2paStatus: ProvenanceStatus;
  signals: ForensicSignal[];
  evidenceItems: EvidenceItem[];
  timelineMarkers: TimelineMarker[];
  modelOutputs: ModelOutput[];
  robustnessResults: RobustnessTestResult[];
  provenanceGraph: ProvenanceNode[];
  
  // Forensic Explanation Engine Payload
  explanation?: ForensicExplanation;

  // Media asset previews
  previewUrl?: string;
  audioWaveformData?: number[];
  transcript?: { time: string; speaker: string; text: string; suspicious: boolean }[];
}

export type ForensicMediaItem = ForensicCase;

