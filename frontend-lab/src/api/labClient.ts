const LAB_API_BASE = import.meta.env.VITE_LAB_API_BASE ?? "http://localhost:8000";
const LAB_TOKEN = import.meta.env.VITE_LAB_TOKEN ?? "";

export async function labGet<T>(path: string): Promise<T> {
  const response = await fetch(`${LAB_API_BASE}${path}`, {
    headers: { "X-Lab-Token": LAB_TOKEN },
  });
  if (!response.ok) {
    throw new Error(`lab request to ${path} failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function labPost<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${LAB_API_BASE}${path}`, {
    method: "POST",
    headers: { "X-Lab-Token": LAB_TOKEN, "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    throw new Error(`lab request to ${path} failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}
