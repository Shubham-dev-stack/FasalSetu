import { AuthResponse, ReferenceDataResponse, User } from './types';

export interface HealthResponse {
  status: string;
  db: string;
  model: {
    loaded: boolean;
    deployed_method: string;
  };
  demo_mode: boolean;
  version: string;
}

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

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`);
  return handleResponse<HealthResponse>(response);
}

export async function loginApi(username: string, password: string): Promise<AuthResponse> {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData.toString(),
  });
  return handleResponse<AuthResponse>(response);
}

export async function demoLoginApi(persona: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE}/auth/demo-login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ persona }),
  });
  return handleResponse<AuthResponse>(response);
}

export async function fetchMeApi(token: string): Promise<User> {
  const response = await fetch(`${API_BASE}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return handleResponse<User>(response);
}

export async function fetchReferenceDataApi(): Promise<ReferenceDataResponse> {
  const response = await fetch(`${API_BASE}/reference`);
  return handleResponse<ReferenceDataResponse>(response);
}
