import {
  AnalyticsOverviewResponse,
  AnalyticsSupplyDemandResponse,
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = res.statusText;
    try {
      const body = await res.json();
      if (body?.error?.message) {
        errorDetail = body.error.message;
      } else if (body?.detail) {
        errorDetail =
          typeof body.detail === 'string'
            ? body.detail
            : JSON.stringify(body.detail);
      }
    } catch {
      // Non-JSON response
    }
    throw new Error(errorDetail || `HTTP ${res.status}`);
  }
  return res.json();
}

function getAuthHeaders(token?: string | null): Record<string, string> {
  const headers: Record<string, string> = {};
  const effectiveToken = token || localStorage.getItem('token');
  if (effectiveToken) {
    headers.Authorization = `Bearer ${effectiveToken}`;
  }
  return headers;
}

export async function fetchAnalyticsOverviewApi(
  token?: string | null
): Promise<AnalyticsOverviewResponse> {
  const response = await fetch(`${API_BASE}/analytics/overview`, {
    headers: getAuthHeaders(token),
  });
  return handleResponse<AnalyticsOverviewResponse>(response);
}

export async function fetchAnalyticsSupplyDemandApi(
  cropId?: number | null,
  token?: string | null
): Promise<AnalyticsSupplyDemandResponse> {
  const url = cropId
    ? `${API_BASE}/analytics/supply-demand?crop_id=${cropId}`
    : `${API_BASE}/analytics/supply-demand`;
  const response = await fetch(url, {
    headers: getAuthHeaders(token),
  });
  return handleResponse<AnalyticsSupplyDemandResponse>(response);
}
