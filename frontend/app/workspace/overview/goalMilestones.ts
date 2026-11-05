import type { RecentCalculationSummary } from "@/lib/api/generated";
import type { WorkspaceState } from "@/lib/api/workspace";

export type GoalMilestone = { id: string; label: string; done: boolean; href: string };

const MIN_SKILLS = 3;

/**
 * Every step towards the user's goal, in the order they are usually done.
 * Pure and deterministic: each step is derived from stored data, nothing is estimated.
 * Roadmap tasks are included one by one, but only for users who can open the roadmap.
 */
export function buildGoalMilestones(workspace: WorkspaceState, calculations: RecentCalculationSummary[], includeRoadmap: boolean): GoalMilestone[] {
  const { profile, connections, saved_course_ids: savedCourses, roadmap } = workspace;
  const milestones: GoalMilestone[] = [
    { id: "account", label: "Create your Fence account", done: true, href: "/workspace/profile" },
    { id: "profile", label: "Add field of study and country to your profile", done: Boolean(profile.field_of_study.trim() && profile.country.trim()), href: "/workspace/profile" },
    { id: "skills", label: `List at least ${MIN_SKILLS} current skills`, done: profile.skills.length >= MIN_SKILLS, href: "/workspace/profile" },
    { id: "target", label: "Set a career target", done: Boolean(profile.career_target?.trim() || roadmap?.target_job), href: "/workspace/profile" },
    { id: "calculation", label: "Save your first calculation", done: calculations.length > 0, href: "/workspace/scenario/new" },
    { id: "forecast", label: "Compute an ROI forecast", done: calculations.some((item) => item.projection_id != null), href: "/workspace/scenarios" },
    { id: "alternative", label: "Save a second scenario to compare paths", done: calculations.length > 1, href: "/workspace/scenario/new" },
    { id: "course", label: "Save a course from the catalog", done: savedCourses.length > 0, href: "/workspace/courses" },
    { id: "platform", label: "Connect an external platform", done: Object.values(connections).some((item) => item.connected), href: "/workspace/settings" },
  ];
  if (includeRoadmap) {
    milestones.push({ id: "roadmap", label: "Create a career roadmap", done: roadmap != null, href: "/workspace/roadmap/simulation" });
    for (const phase of roadmap?.plan?.phases ?? []) {
      for (const task of phase.tasks ?? []) {
        milestones.push({ id: `task-${phase.id}-${task.id}`, label: `${task.title} (${phase.title})`, done: task.completed, href: "/workspace/roadmap/plan" });
      }
    }
  }
  return milestones;
}

export function goalPercent(milestones: GoalMilestone[]): number {
  if (!milestones.length) return 0;
  return Math.round((milestones.filter((item) => item.done).length / milestones.length) * 100);
}
