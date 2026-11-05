import { apiRequest } from "./client";

import type {
  WorkspaceCourseResponse,
  WorkspaceProfile as GeneratedWorkspaceProfile,
  WorkspaceRoadmapSummary,
  WorkspaceStateResponse,
  WorkspaceUniversityDetailsResponse,
  WorkspaceUniversityResponse,
  UniversityProfileResponse,
} from "./generated";

export type WorkspaceProfile = GeneratedWorkspaceProfile;

// The normalized roadmap plan is still a free-form dict on the backend (WorkspaceRoadmapSummary.plan);
// these shapes mirror what app/services/workspace_service.normalize_roadmap produces.
export type RoadmapTask = { id: string; title: string; description: string; completed: boolean };
export type RoadmapPhase = { id: string; title: string; hours: number; weeks: number; skills: string[]; tasks?: RoadmapTask[] };
export type RoadmapPlan = { target_job: string; current_level: string; hours_per_week: number; skills: string[]; total_hours: number; weeks: number; phases: RoadmapPhase[] };

export type WorkspaceConnection = { connected: boolean; available: boolean; label: string };

export type WorkspaceState = Omit<WorkspaceStateResponse, "connections" | "roadmap"> & {
  // Server-side defaults guarantee these three keys for every connection.
  connections: Record<string, WorkspaceConnection>;
  roadmap: null | (Omit<WorkspaceRoadmapSummary, "plan"> & { plan: RoadmapPlan });
};

export type WorkspaceCourse = WorkspaceCourseResponse;

export type WorkspaceUniversity = WorkspaceUniversityResponse;

// Stored catalogue records are free-form dicts on the backend; these mirror workspace_service.university_details.
export type WorkspaceUniversityDetails = Omit<WorkspaceUniversityDetailsResponse, "programmes" | "documents" | "scholarships"> & {
  programmes: Array<{ id: string | number; name: string; description: string | null; duration_years: number; tuition_cost: number }>;
  documents: Array<{ id: number; title: string; subject_name: string; source_url: string }>;
  scholarships: Array<{ id: number; name: string; description: string | null; amount: number | null; currency: string | null; eligibility: string | null; application_url: string | null; deadline: string | null }>;
};
export type UniversityProfile = UniversityProfileResponse;

export function workspaceFetch<T>(url: string, init: RequestInit = {}): Promise<T> {
  return apiRequest<T>(url, {
    ...init,
    authenticated: true,
    fallbackMessage: "Fence could not complete this workspace request.",
  });
}
