import {
  Requirement,
  RequirementCreateRequest,
  RequirementDetailResponse,
  RequirementListResponse,
  RequirementUpdateRequest,
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

export async function fetchRequirementsApi(params: {
  token: string;
  crop_id?: number;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<RequirementListResponse> {
  const query = new URLSearchParams();
  if (params.crop_id) query.append('crop_id', String(params.crop_id));
  if (params.status) query.append('status', params.status);
  if (params.limit) query.append('limit', String(params.limit));
  if (params.offset) query.append('offset', String(params.offset));

  const url = `${API_BASE}/requirements${query.toString() ? `?${query.toString()}` : ''}`;
  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${params.token}`,
    },
  });
  return handleResponse<RequirementListResponse>(response);
}

export async function fetchRequirementByIdApi(
  token: string,
  id: number
): Promise<RequirementDetailResponse> {
  const response = await fetch(`${API_BASE}/requirements/${id}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return handleResponse<RequirementDetailResponse>(response);
}

export async function createRequirementApi(
  token: string,
  payload: RequirementCreateRequest
): Promise<Requirement> {
  const response = await fetch(`${API_BASE}/requirements`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<Requirement>(response);
}

export async function updateRequirementApi(
  token: string,
  id: number,
  payload: RequirementUpdateRequest
): Promise<Requirement> {
  const response = await fetch(`${API_BASE}/requirements/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<Requirement>(response);
}
