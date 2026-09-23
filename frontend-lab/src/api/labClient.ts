const LAB_API_BASE = import.meta.env.VITE_LAB_API_BASE ?? "http://localhost:8000";
export const AGENT_URL = import.meta.env.VITE_AGENT_URL ?? "http://localhost:5173";

// Auth is a session cookie (see POST /lab/login), never a token embedded
// in this bundle — credentials: "include" sends/receives it across the
// (cross-origin, once hosted) Vercel<->Railway boundary. The backend's
// CORS layer echoes this origin specifically and sets
// Access-Control-Allow-Credentials, which is required for this to work.
export class LabApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function labFetch(path: string, init: RequestInit = {}): Promise<Response> {
  return fetch(`${LAB_API_BASE}${path}`, { ...init, credentials: "include" });
}

export async function labGet<T>(path: string): Promise<T> {
  const response = await labFetch(path);
  if (!response.ok) {
    throw new LabApiError(response.status, `lab request to ${path} failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function labPost<T>(path: string, body?: unknown): Promise<T> {
  const response = await labFetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    throw new LabApiError(response.status, `lab request to ${path} failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}
