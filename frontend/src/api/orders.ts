import {
  Order,
  OrderCreateRequest,
  OrderListResponse,
  OrderTransitionRequest,
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
          typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // Non-JSON response
    }
    throw new Error(errorDetail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchOrdersApi(
  token: string,
  params?: {
    status?: string;
    crop_id?: number;
    limit?: number;
    offset?: number;
  }
): Promise<OrderListResponse> {
  const query = new URLSearchParams();
  if (params?.status) query.append('status', params.status);
  if (params?.crop_id) query.append('crop_id', String(params.crop_id));
  if (params?.limit) query.append('limit', String(params.limit));
  if (params?.offset) query.append('offset', String(params.offset));

  const url = `${API_BASE}/orders${query.toString() ? `?${query.toString()}` : ''}`;
  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return handleResponse<OrderListResponse>(response);
}

export async function fetchOrderByIdApi(token: string, id: number): Promise<Order> {
  const response = await fetch(`${API_BASE}/orders/${id}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return handleResponse<Order>(response);
}

export async function createOrderApi(
  token: string,
  payload: OrderCreateRequest
): Promise<Order> {
  const response = await fetch(`${API_BASE}/orders`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<Order>(response);
}

export async function transitionOrderApi(
  token: string,
  id: number,
  payload: OrderTransitionRequest
): Promise<Order> {
  const response = await fetch(`${API_BASE}/orders/${id}/transition`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<Order>(response);
}
