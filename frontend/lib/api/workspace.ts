import { apiRequest } from "./client";

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

export type WorkspaceUniversityDetails = WorkspaceUniversity & {
  programmes: Array<{ id: string | number; name: string; description: string | null; duration_years: number; tuition_cost: number }>;
  documents: Array<{ id: number; title: string; subject_name: string; source_url: string }>;
  scholarships: Array<{ id: number; name: string; description: string | null; amount: number | null; currency: string | null; eligibility: string | null; application_url: string | null; deadline: string | null }>;
};

export function workspaceFetch<T>(url: string, init: RequestInit = {}): Promise<T> {
  return apiRequest<T>(url, {
    ...init,
    authenticated: true,
    fallbackMessage: "Fence could not complete this workspace request.",
  });
}
