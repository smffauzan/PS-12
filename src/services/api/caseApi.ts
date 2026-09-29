import { apiFetch } from './client';
import type { ForensicCase } from '../../types/forensics';

export interface CaseSummaryItem {
  case_id: string;
  media_id: string;
  filename: string;
  media_type: string;
  risk_score: number;
  risk_tier: string;
  confidence: number;
  consensus: number;
  signal_count: number;
  timestamp: string;
  status: string;
}

export interface CaseListApiResponse {
  cases: CaseSummaryItem[];
  total: number;
}

export async function fetchCasesList(): Promise<CaseListApiResponse | null> {
  return await apiFetch<CaseListApiResponse>('/api/v1/cases');
}

export async function fetchCaseDetails(caseId: string): Promise<ForensicCase | null> {
  return await apiFetch<ForensicCase>(`/api/v1/cases/${encodeURIComponent(caseId)}`);
}

export async function createNewCase(
  filename: string,
  mediaType: string,
  caseId?: string
): Promise<ForensicCase | null> {
  return await apiFetch<ForensicCase>('/api/v1/cases', {
    method: 'POST',
    body: JSON.stringify({
      filename,
      media_type: mediaType,
      case_id: caseId
    })
  });
}
