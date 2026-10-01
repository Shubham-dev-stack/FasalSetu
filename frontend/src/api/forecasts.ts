import {
  ForecastDemandResponse,
  ForecastHubsResponse,
  ModelInfoResponse,
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
        errorDetail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // Non-JSON response
    }
    throw new Error(errorDetail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function getDemandForecast(
  hubId: number,
  cropId: number,
  horizonDays: number = 7,
  cutoffDate?: string,
): Promise<ForecastDemandResponse> {
  const params = new URLSearchParams({
    hub_id: hubId.toString(),
    crop_id: cropId.toString(),
    horizon_days: horizonDays.toString(),
  });
  if (cutoffDate) {
    params.set('cutoff_date', cutoffDate);
  }

  const res = await fetch(`${API_BASE}/forecasts/demand?${params.toString()}`);
  return handleResponse<ForecastDemandResponse>(res);
}

export async function getHubsForecast(
  cropId: number,
  horizonDays: number = 7,
  cutoffDate?: string,
): Promise<ForecastHubsResponse> {
  const params = new URLSearchParams({
    crop_id: cropId.toString(),
    horizon_days: horizonDays.toString(),
  });
  if (cutoffDate) {
    params.set('cutoff_date', cutoffDate);
  }

  const res = await fetch(`${API_BASE}/forecasts/hubs?${params.toString()}`);
  return handleResponse<ForecastHubsResponse>(res);
}

export async function getModelInfo(): Promise<ModelInfoResponse> {
  const res = await fetch(`${API_BASE}/forecasts/model-info`);
  return handleResponse<ModelInfoResponse>(res);
}
