export const AUTH_EXPIRED_EVENT = "fence:auth-expired";

type ApiErrorPayload = {
  detail?: string | Array<{ msg?: string }>;
  message?: string;
};

type ApiRequestInit = RequestInit & {
  authenticated?: boolean;
  fallbackMessage?: string;
};

export class ApiRequestError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
  }
}

export function readCookie(name: string): string {
  if (typeof document === "undefined") return "";
  const prefix = `${name}=`;
  const cookie = document.cookie.split("; ").find((item) => item.startsWith(prefix));
  return cookie ? decodeURIComponent(cookie.slice(prefix.length)) : "";
}

export function getCsrfToken(): string {
  return readCookie("csrf_token");
}

function errorMessage(payload: ApiErrorPayload, fallback: string): string {
  if (typeof payload.detail === "string") return payload.detail;
  if (Array.isArray(payload.detail)) {
    const messages = payload.detail.map((item) => item.msg).filter(Boolean);
    if (messages.length) return messages.join(". ").replace(/^Value error,\s*/i, "");
  }
  return payload.message || fallback;
}

export async function apiRequest<T>(url: string, init: ApiRequestInit = {}): Promise<T> {
  const { authenticated = false, fallbackMessage = "Fence could not complete this request.", ...requestInit } = init;
  const method = (requestInit.method || "GET").toUpperCase();
  const headers = new Headers(requestInit.headers);
  headers.set("Accept", "application/json");
  if (requestInit.body && !(requestInit.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (!["GET", "HEAD", "OPTIONS"].includes(method) && !headers.has("X-CSRF-Token")) {
    const csrfToken = getCsrfToken();
    if (csrfToken) headers.set("X-CSRF-Token", csrfToken);
  }

  const response = await fetch(url, {
    ...requestInit,
    method,
    headers,
    credentials: "include",
  });
  const payload = response.status === 204
    ? null
    : await response.json().catch(() => ({} as ApiErrorPayload));

  if (!response.ok) {
    if (authenticated && response.status === 401 && typeof window !== "undefined") {
      window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
    }
    throw new ApiRequestError(errorMessage(payload as ApiErrorPayload, fallbackMessage), response.status);
  }

  return payload as T;
}
