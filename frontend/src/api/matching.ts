import {
  MatchingAcceptRequest,
  MatchingAcceptResponse,
  MatchingCandidatesResponse,
  ProducerOpportunitiesResponse,
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

export async function fetchRequirementCandidatesApi(
  token: string,
  requirementId: number,
  maxResults?: number
): Promise<MatchingCandidatesResponse> {
  const query = new URLSearchParams();
  if (maxResults) query.append('max_results', String(maxResults));

  const qs = query.toString() ? `?${query.toString()}` : '';
  const res = await fetch(`${API_BASE}/matching/requirements/${requirementId}/candidates${qs}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return handleResponse<MatchingCandidatesResponse>(res);
}

export async function acceptMatchingAllocationApi(
  token: string,
  data: MatchingAcceptRequest
): Promise<MatchingAcceptResponse> {
  const res = await fetch(`${API_BASE}/matching/accept`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  return handleResponse<MatchingAcceptResponse>(res);
}

export async function fetchListingOpportunitiesApi(
  token: string,
  listingId: number,
  limit?: number
): Promise<ProducerOpportunitiesResponse> {
  const query = new URLSearchParams();
  if (limit) query.append('limit', String(limit));

  const qs = query.toString() ? `?${query.toString()}` : '';
  const res = await fetch(`${API_BASE}/matching/listings/${listingId}/opportunities${qs}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return handleResponse<ProducerOpportunitiesResponse>(res);
}
