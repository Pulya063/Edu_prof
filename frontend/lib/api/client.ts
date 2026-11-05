export const AUTH_EXPIRED_EVENT = "fence:auth-expired";

/** One Pydantic validation error as returned by the Flask 422 handler. */
export type ValidationIssue = { type?: string; loc?: Array<string | number>; msg?: string };

type ApiErrorPayload = {
  detail?: string | ValidationIssue[];
  message?: string;
};

type ApiRequestInit = RequestInit & {
  authenticated?: boolean;
  fallbackMessage?: string;
};

/** Field path ("assumptions.annual_tuition") -> human message. Errors without a field land in "". */
export type FieldErrors = Record<string, string>;

export class ApiRequestError extends Error {
  readonly status: number;
  readonly fieldErrors: FieldErrors;

  constructor(message: string, status: number, fieldErrors: FieldErrors = {}) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

const ISSUE_MESSAGES: Record<string, string> = {
  missing: "This field is required.",
  string_too_short: "This value is too short.",
  string_too_long: "This value is too long.",
  too_short: "Add at least one item.",
  too_long: "Too many items.",
  decimal_parsing: "Enter a number.",
  float_parsing: "Enter a number.",
  int_parsing: "Enter a whole number.",
  decimal_max_places: "Too many decimal places.",
  decimal_max_digits: "This number is too large.",
  value_error: "",
  extra_forbidden: "This field is not accepted.",
  literal_error: "Choose one of the listed options.",
  enum: "Choose one of the listed options.",
  date_parsing: "Enter a valid date.",
  datetime_parsing: "Enter a valid date and time.",
};

/** Turn a Pydantic issue into a short, user-facing sentence. */
export function humanizeIssue(issue: ValidationIssue): string {
  const raw = (issue.msg || "").replace(/^Value error,\s*/i, "").trim();
  const mapped = issue.type ? ISSUE_MESSAGES[issue.type] : undefined;
  if (mapped) return mapped;
  // Bound checks keep the limit from Pydantic's text: "Input should be greater than 0" -> "Must be greater than 0."
  const bound = raw.match(/^Input should be (.+)$/i);
  if (bound) return `Must be ${bound[1].replace(/\.$/, "")}.`;
  return raw || "This value is not valid.";
}

function fieldLabel(loc: ValidationIssue["loc"]): string {
  const last = [...(loc || [])].reverse().find((part) => typeof part === "string") as string | undefined;
  if (!last) return "Value";
  const words = last.replaceAll("_", " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

export function toFieldErrors(detail: ApiErrorPayload["detail"]): FieldErrors {
  if (!Array.isArray(detail)) return {};
  const errors: FieldErrors = {};
  for (const issue of detail) {
    const key = (issue.loc || []).join(".");
    if (!(key in errors)) errors[key] = humanizeIssue(issue);
  }
  return errors;
}

/** First message for a field or any of its children ("assumptions" matches "assumptions.degree"). */
export function fieldError(errors: FieldErrors, field: string): string | undefined {
  if (errors[field]) return errors[field];
  const nested = Object.keys(errors).find((key) => key.endsWith(`.${field}`) || key.startsWith(`${field}.`));
  return nested ? errors[nested] : undefined;
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
  if (Array.isArray(payload.detail) && payload.detail.length) {
    const formLevel = payload.detail.find((issue) => !issue.loc?.length);
    if (formLevel) return humanizeIssue(formLevel);
    // Name the field so pages without inline field errors still tell the user what to fix.
    return payload.detail.slice(0, 3).map((issue) => `${fieldLabel(issue.loc)}: ${humanizeIssue(issue)}`).join(" ");
  }
  return payload.message || fallback;
}

/** Read an error body from a raw fetch Response (for pages that do not use apiRequest). */
export async function readApiError(response: Response, fallback: string): Promise<ApiRequestError> {
  const payload = await response.json().catch(() => ({} as ApiErrorPayload)) as ApiErrorPayload;
  return new ApiRequestError(errorMessage(payload, fallback), response.status, toFieldErrors(payload.detail));
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
    const errorPayload = (payload ?? {}) as ApiErrorPayload;
    throw new ApiRequestError(errorMessage(errorPayload, fallbackMessage), response.status, toFieldErrors(errorPayload.detail));
  }

  return payload as T;
}
