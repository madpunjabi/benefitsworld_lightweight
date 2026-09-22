// The ONLY backend this app ever talks to is the public router. There is
// no lab origin, no lab token, and no /lab reference anywhere in this
// package — that absence is what agent_frontend_isolation.spec.ts checks
// for in the built production bundle.
const API_BASE = "http://localhost:8000";

export async function getJSON<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`request to ${path} failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`request to ${path} failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}
