function resolveApiBase(): string {
  const raw = (import.meta.env.VITE_API_URL || "/api/v1").trim().replace(/\/+$/, "");
  if (raw.endsWith("/api/v1")) return raw;
  if (raw.startsWith("http://") || raw.startsWith("https://")) {
    return `${raw}/api/v1`;
  }
  return raw;
}

export const API_BASE = resolveApiBase();

export function getStoredToken(): string | null {
  return localStorage.getItem("aip_token");
}

export function setStoredToken(token: string | null): void {
  if (token) {
    localStorage.setItem("aip_token", token);
  } else {
    localStorage.removeItem("aip_token");
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const err = await res.json();
      if (typeof err.detail === "string") message = err.detail;
      else if (Array.isArray(err.detail) && err.detail[0]?.msg) {
        message = err.detail[0].msg;
      }
    } catch {
      // keep default message
    }
    throw new Error(message);
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}
