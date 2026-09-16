export interface HealthStatusResponse {
  status: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Calls the backend GET /api/health endpoint.
 *
 * @returns Promise resolving to the typed health status object.
 */
export async function getHealthStatus(): Promise<HealthStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`);
  }

  return response.json();
}
