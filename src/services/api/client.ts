const API_BASE_URL = typeof window !== 'undefined' && window.location.port === '5173'
  ? '' // Use Vite proxy in development
  : 'http://127.0.0.1:8000';

export interface BackendHealthStatus {
  isConnected: boolean;
  engine?: string;
  version?: string;
}

let isBackendAvailable: boolean | null = null;

export async function checkBackendConnection(): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const res = await fetch(`${API_BASE_URL}/health`, {
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (res.ok) {
      isBackendAvailable = true;
      return true;
    }
    isBackendAvailable = false;
    return false;
  } catch {
    isBackendAvailable = false;
    return false;
  }
}

export function getIsBackendConnected(): boolean {
  return isBackendAvailable === true;
}

export async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T | null> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {})
      },
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      const errText = await res.text().catch(() => '');
      console.warn(`[VERITAS API] ${endpoint} returned HTTP ${res.status}:`, errText);
      return null;
    }

    return (await res.json()) as T;
  } catch (err) {
    console.error(`[VERITAS API] ${endpoint} fetch failed:`, err);
    return null;
  }
}

export async function apiUpload<T>(endpoint: string, formData: FormData): Promise<T | null> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s for multi-frame CPU video inference

    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      body: formData,
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      const errJson = await res.json().catch(() => null);
      const errText = errJson?.detail?.message || errJson?.detail || (await res.text().catch(() => 'Upload failed'));
      console.error(`[VERITAS API] Upload error (${res.status}):`, errText);
      throw new Error(typeof errText === 'string' ? errText : JSON.stringify(errText));
    }

    return (await res.json()) as T;
  } catch (err: any) {
    console.error(`[VERITAS API] ${endpoint} upload request failed:`, err);
    throw err;
  }
}

