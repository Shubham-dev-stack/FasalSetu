import {
  OptimizeRoutesRequest,
  RoutePlanApproveResponse,
  RoutePlanListResponse,
  RoutePlanResponse,
  ShipmentDetailResponse,
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
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  const effectiveToken = token || localStorage.getItem('token');
  if (effectiveToken) {
    headers.Authorization = `Bearer ${effectiveToken}`;
  }
  return headers;
}

export async function optimizeRoutesApi(
  req: OptimizeRoutesRequest = {},
  token?: string | null
): Promise<RoutePlanResponse> {
  const response = await fetch(`${API_BASE}/routes/optimize`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify(req),
  });
  return handleResponse<RoutePlanResponse>(response);
}

export async function fetchRoutePlansApi(
  statusFilter?: string,
  token?: string | null
): Promise<RoutePlanListResponse> {
  const query = new URLSearchParams();
  if (statusFilter) query.append('status_filter', statusFilter);
  const url = `${API_BASE}/routes/plans${query.toString() ? `?${query.toString()}` : ''}`;
  const response = await fetch(url, {
    headers: getAuthHeaders(token),
  });
  return handleResponse<RoutePlanListResponse>(response);
}

export async function fetchRoutePlanDetailApi(
  planId: string,
  token?: string | null
): Promise<RoutePlanResponse> {
  const response = await fetch(`${API_BASE}/routes/plans/${planId}`, {
    headers: getAuthHeaders(token),
  });
  return handleResponse<RoutePlanResponse>(response);
}

export async function approveRoutePlanApi(
  planId: string,
  token?: string | null
): Promise<RoutePlanApproveResponse> {
  const response = await fetch(`${API_BASE}/routes/plans/${planId}/approve`, {
    method: 'POST',
    headers: getAuthHeaders(token),
  });
  return handleResponse<RoutePlanApproveResponse>(response);
}

export async function discardRoutePlanApi(
  planId: string,
  token?: string | null
): Promise<RoutePlanResponse> {
  const response = await fetch(`${API_BASE}/routes/plans/${planId}/discard`, {
    method: 'POST',
    headers: getAuthHeaders(token),
  });
  return handleResponse<RoutePlanResponse>(response);
}

export async function fetchShipmentApi(
  shipmentId: number,
  token?: string | null
): Promise<ShipmentDetailResponse> {
  const response = await fetch(`${API_BASE}/routes/shipments/${shipmentId}`, {
    headers: getAuthHeaders(token),
  });
  return handleResponse<ShipmentDetailResponse>(response);
}

export async function transitionShipmentApi(
  shipmentId: number,
  toStatus: 'DISPATCHED' | 'DELIVERED',
  token?: string | null
): Promise<ShipmentDetailResponse> {
  const response = await fetch(`${API_BASE}/routes/shipments/${shipmentId}/transition`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ to_status: toStatus }),
  });
  return handleResponse<ShipmentDetailResponse>(response);
}
