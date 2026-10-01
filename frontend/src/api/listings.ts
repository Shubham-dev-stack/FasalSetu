import {
  Listing,
  ListingCreateRequest,
  ListingCreateResponse,
  ListingDetailResponse,
  ListingListResponse,
  ListingUpdateRequest,
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

export async function fetchListingsApi(params?: {
  crop_id?: number;
  grade_min?: string;
  state?: string;
  max_price?: number;
  status?: string;
  mine?: boolean;
  limit?: number;
  offset?: number;
  token?: string | null;
}): Promise<ListingListResponse> {
  const query = new URLSearchParams();
  if (params?.crop_id) query.append('crop_id', String(params.crop_id));
  if (params?.grade_min) query.append('grade_min', params.grade_min);
  if (params?.state) query.append('state', params.state);
  if (params?.max_price) query.append('max_price', String(params.max_price));
  if (params?.status) query.append('status', params.status);
  if (params?.mine) query.append('mine', 'true');
  if (params?.limit) query.append('limit', String(params.limit));
  if (params?.offset) query.append('offset', String(params.offset));

  const headers: HeadersInit = {};
  if (params?.token) {
    headers['Authorization'] = `Bearer ${params.token}`;
  }

  const url = `${API_BASE}/listings${query.toString() ? `?${query.toString()}` : ''}`;
  const response = await fetch(url, { headers });
  return handleResponse<ListingListResponse>(response);
}

export async function fetchListingByIdApi(id: number): Promise<ListingDetailResponse> {
  const response = await fetch(`${API_BASE}/listings/${id}`);
  return handleResponse<ListingDetailResponse>(response);
}

export async function createListingApi(
  token: string,
  payload: ListingCreateRequest
): Promise<ListingCreateResponse> {
  const response = await fetch(`${API_BASE}/listings`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<ListingCreateResponse>(response);
}

export async function updateListingApi(
  token: string,
  id: number,
  payload: ListingUpdateRequest
): Promise<Listing> {

  const response = await fetch(`${API_BASE}/listings/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<Listing>(response);
}

