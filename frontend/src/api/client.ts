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

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }
  return response.json();
}
