import {
  LogisticsEstimateRequest,
  LogisticsEstimateResponse,
  VehicleListResponse,
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

export async function fetchLogisticsEstimateApi(
  req: LogisticsEstimateRequest,
  token?: string | null
): Promise<LogisticsEstimateResponse> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}/logistics/estimate`, {
    method: 'POST',
    headers,
    body: JSON.stringify(req),
  });
  return handleResponse<LogisticsEstimateResponse>(response);
}

export async function fetchVehiclesApi(
  token?: string | null
): Promise<VehicleListResponse> {
  const headers: Record<string, string> = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}/logistics/vehicles`, {
    headers,
  });
  return handleResponse<VehicleListResponse>(response);
}
