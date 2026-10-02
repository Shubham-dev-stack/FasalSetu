import {
  OrderPriceBreakdownResponse,
  PricingBenchmarkResponse,
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

export async function fetchOrderPriceBreakdownApi(
  orderId: number,
  token?: string | null
): Promise<OrderPriceBreakdownResponse> {
  const response = await fetch(`${API_BASE}/pricing/breakdown?order_id=${orderId}`, {
    headers: getAuthHeaders(token),
  });
  return handleResponse<OrderPriceBreakdownResponse>(response);
}

export async function fetchPricingBenchmarkApi(
  params: {
    crop_id: number;
    hub_id?: number;
    lat?: number;
    lng?: number;
    quantity_kg?: number;
  },
  token?: string | null
): Promise<PricingBenchmarkResponse> {
  const query = new URLSearchParams();
  query.append('crop_id', String(params.crop_id));
  if (params.hub_id !== undefined) query.append('hub_id', String(params.hub_id));
  if (params.lat !== undefined) query.append('lat', String(params.lat));
  if (params.lng !== undefined) query.append('lng', String(params.lng));
  if (params.quantity_kg !== undefined) query.append('quantity_kg', String(params.quantity_kg));

  const response = await fetch(`${API_BASE}/pricing/benchmark?${query.toString()}`, {
    headers: getAuthHeaders(token),
  });
  return handleResponse<PricingBenchmarkResponse>(response);
}
