import {
  BuyerProfileOut,
  BuyerProfileUpdate,
  ProducerProfileOut,
  ProducerProfileUpdate,
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

export async function fetchProducerProfileApi(token: string): Promise<ProducerProfileOut> {
  const response = await fetch(`${API_BASE}/producers/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return handleResponse<ProducerProfileOut>(response);
}

export async function updateProducerProfileApi(
  token: string,
  payload: ProducerProfileUpdate
): Promise<ProducerProfileOut> {
  const response = await fetch(`${API_BASE}/producers/me`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<ProducerProfileOut>(response);
}

export async function fetchBuyerProfileApi(token: string): Promise<BuyerProfileOut> {
  const response = await fetch(`${API_BASE}/buyers/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return handleResponse<BuyerProfileOut>(response);
}

export async function updateBuyerProfileApi(
  token: string,
  payload: BuyerProfileUpdate
): Promise<BuyerProfileOut> {
  const response = await fetch(`${API_BASE}/buyers/me`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<BuyerProfileOut>(response);
}
