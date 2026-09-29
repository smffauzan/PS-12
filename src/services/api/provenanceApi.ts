import { apiFetch } from './client';

export interface ProvenanceCheckApiResponse {
  status: string;
  manifest_found: boolean;
  provenance_statement: string;
  provenance_graph: Array<Record<string, unknown>>;
}

export async function requestProvenanceCheck(sha256: string): Promise<ProvenanceCheckApiResponse | null> {
  return await apiFetch<ProvenanceCheckApiResponse>('/api/v1/provenance/check', {
    method: 'POST',
    body: JSON.stringify({ sha256 })
  });
}
