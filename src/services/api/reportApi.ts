import { apiFetch } from './client';

export interface ReportApiResponse {
  report_id: string;
  generated_at: string;
  case_data: Record<string, unknown>;
  verification_url: string;
  status: string;
  signature: string;
}

export async function requestReportGeneration(caseId: string): Promise<ReportApiResponse | null> {
  return await apiFetch<ReportApiResponse>(`/api/v1/reports/${encodeURIComponent(caseId)}`, {
    method: 'POST'
  });
}
