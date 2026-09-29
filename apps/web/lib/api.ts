export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/management/${path.replace(/^\//, "")}`, {
      ...init,
      signal: init?.signal ?? AbortSignal.timeout(10_000),
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError(503, "Management API is unavailable. Check system health and retry.");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new ApiError(response.status, body.detail ?? "Request failed");
  }
  return response.json() as Promise<T>;
}
