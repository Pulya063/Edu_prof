export type WorkspaceProfile = {
  field_of_study: string;
  country: string;
  about: string;
  skills: string[];
  career_target: string | null;
};

export type RoadmapTask = { id: string; title: string; description: string; completed: boolean };
export type RoadmapPhase = { id: string; title: string; hours: number; weeks: number; skills: string[]; tasks?: RoadmapTask[] };
export type RoadmapPlan = { target_job: string; current_level: string; hours_per_week: number; skills: string[]; total_hours: number; weeks: number; phases: RoadmapPhase[] };

export type WorkspaceState = {
  user: { id: number; username: string; email: string; plan: string; scenario_count: number };
  profile: WorkspaceProfile;
  preferences: { language: "English" | "Українська"; currency: "USD" | "EUR" | "PLN" | "GBP"; theme: "Fence default" };
  connections: Record<string, { connected: boolean; available: boolean; label: string }>;
  saved_course_ids: string[];
  roadmap: null | { id: number; target_job: string; updated_at: string; plan: RoadmapPlan };
};

export type WorkspaceCourse = {
  id: string; title: string; description: string; level: string; language: string;
  format: string; duration: string; skills: string[]; provider_name: string;
  provider_url: string | null; saved: boolean;
};

export type WorkspaceUniversity = {
  id: string; name: string; country: string; city: string | null; website: string | null;
  description: string; annual_tuition: number | null; currency: string;
  duration_years: number | null; study_mode: string; program_name: string;
  data_quality: "database" | "illustrative";
};

function csrfToken() {
  if (typeof document === "undefined") return "";
  const cookie = document.cookie.split("; ").find((item) => item.startsWith("csrf_token="));
  return cookie ? decodeURIComponent(cookie.split("=").slice(1).join("=")) : "";
}

export async function workspaceFetch<T>(url: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method || "GET").toUpperCase();
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body) headers.set("Content-Type", "application/json");
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) headers.set("X-CSRF-Token", csrfToken());

  const response = await fetch(url, { ...init, headers, credentials: "include" });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(payload?.detail)
      ? payload.detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join(". ")
      : payload?.detail || payload?.message;
    throw new Error(detail || "Fence could not complete this request.");
  }
  return payload as T;
}
