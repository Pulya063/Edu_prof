"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api/client";
import { formatMoney, formatPercent } from "@/lib/api/decimal";
import type { RecentCalculationSummary, SimulationOverviewResponse } from "@/lib/api/generated";
import { type RoadmapTask, type WorkspaceCourse, type WorkspaceState, workspaceFetch } from "@/lib/api/workspace";
import { useWorkspaceAuth } from "@/components/auth/WorkspaceAuthGuard";
import GoalProgress from "./GoalProgress";
import { buildGoalMilestones } from "./goalMilestones";
import { MarketCard, PlatformsCard } from "./PlatformCards";
import ResourcesPanel, { RESOURCES_PANEL_ENABLED } from "./ResourcesPanel";
import "../../styles/overview.css";

type LoadState = "loading" | "ready" | "error";
type ActiveTask = RoadmapTask & { phase: string };

const NEW_CALCULATION_HREF = "/workspace/scenario/new";

function formatPayback(months: number | null | undefined): string {
  if (months == null) return "Not reached";
  if (months < 12) return `${months} mo`;
  const years = Math.floor(months / 12);
  const rest = months % 12;
  return rest ? `${years} yr ${rest} mo` : `${years} yr`;
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleDateString("en-GB",{ day: "numeric", month: "short", year: "numeric" });
}

export default function OverviewClient() {
  const { user } = useWorkspaceAuth();
  const showRoadmap = user.is_admin;
  const [overview, setOverview] = useState<SimulationOverviewResponse | null>(null);
  const [workspace, setWorkspace] = useState<WorkspaceState | null>(null);
  const [state, setState] = useState<LoadState>("loading");
  // The course catalog is secondary: if it fails, the dashboard still renders.
  const [courses, setCourses] = useState<WorkspaceCourse[] | null>(null);
  const [coursesFailed, setCoursesFailed] = useState(false);

  const load = useCallback(async (signal?: AbortSignal) => {
    setState("loading");
    try {
      const [overviewData, workspaceData] = await Promise.all([
        apiRequest<SimulationOverviewResponse>("/api/simulations/overview", { signal, authenticated: true }),
        apiRequest<WorkspaceState>("/api/workspace", { signal, authenticated: true }),
      ]);
      setOverview(overviewData);
      setWorkspace(workspaceData);
      setState("ready");
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      setState("error");
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    workspaceFetch<WorkspaceCourse[]>("/api/workspace/courses", { signal: controller.signal })
      .then(setCourses)
      .catch((reason) => { if (reason.name !== "AbortError") setCoursesFailed(true); });
    return () => controller.abort();
  }, [load]);

  if (state === "loading") {
    return <div className="ov-page"><p className="ov-muted" role="status">Loading your workspace…</p></div>;
  }
  if (state === "error" || !overview || !workspace) {
    return (
      <div className="ov-page">
        <div className="ov-card ov-error" role="alert">
          <h2>The dashboard could not load.</h2>
          <p>Your data is safe. Check your connection and try again.</p>
          <button type="button" className="ov-button ov-button--dark" onClick={() => void load()}>Try again</button>
        </div>
      </div>
    );
  }

  const calculations = overview.recent_calculations;
  const roadmap = workspace.roadmap;
  const phases = roadmap?.plan?.phases ?? [];
  const allTasks: ActiveTask[] = phases.flatMap((phase) => (phase.tasks ?? []).map((task) => ({ ...task, phase: phase.title })));
  const doneTasks = allTasks.filter((task) => task.completed).length;
  const activeTasks = allTasks.filter((task) => !task.completed);
  const milestones = buildGoalMilestones(workspace, calculations, showRoadmap);
  const platforms = <PlatformsCard connections={workspace.connections} courses={courses} coursesFailed={coursesFailed} />;
  const goal = workspace.profile.career_target?.trim() || roadmap?.target_job || calculations[0]?.target_role || "your career plan";

  return (
    <div className="ov-page">
      <header className="ov-header">
        <p className="ov-breadcrumb">Workspace <i>/</i> Overview</p>
        <div className="ov-title-row">
          <h1>Hi, {workspace.user.username}. <span className="ov-mark">Your next move.</span></h1>
          <Link href={NEW_CALCULATION_HREF} className="ov-button ov-button--lime">Create calculation <span aria-hidden="true">+</span></Link>
        </div>
      </header>

      <GoalProgress goal={goal} milestones={milestones} />

      <div className="ov-grid">
        <div className="ov-col">
        <section className="ov-card ov-calculations" aria-labelledby="ov-calc-title">
          <div className="ov-card-head">
            <h2 id="ov-calc-title">Recent calculations</h2>
            {calculations.length > 0 && <Link href="/workspace/scenarios" className="ov-link">All calculations →</Link>}
          </div>
          {calculations.length === 0 ? (
            <div className="ov-empty">
              <p><strong>No calculations yet.</strong> Pick a university and a target role, and Fence will show the cost, ROI and payback from stored data or your own figures.</p>
              <Link href={NEW_CALCULATION_HREF} className="ov-button ov-button--dark">Create calculation</Link>
            </div>
          ) : (
            <ul className="ov-calc-list">
              {calculations.map((item) => <CalculationRow key={item.scenario_id} item={item} />)}
            </ul>
          )}
        </section>

        {showRoadmap && <>
        <section className="ov-card ov-roadmap" aria-labelledby="ov-roadmap-title">
          <div className="ov-card-head">
            <h2 id="ov-roadmap-title">Roadmap</h2>
            {roadmap && <span className="ov-pill">{allTasks.length && doneTasks === allTasks.length ? "Completed" : "In progress"}</span>}
          </div>
          {roadmap ? (
            <>
              <p className="ov-roadmap-target">{roadmap.target_job}</p>
              <div className="ov-bar" role="progressbar" aria-valuemin={0} aria-valuemax={allTasks.length} aria-valuenow={doneTasks} aria-label="Roadmap tasks completed">
                <span style={{ width: allTasks.length ? `${(doneTasks / allTasks.length) * 100}%` : "0%" }} />
              </div>
              <p className="ov-muted">{doneTasks} of {allTasks.length} tasks done · {phases.length} phases · updated {formatDate(roadmap.updated_at)}</p>
              <Link href="/workspace/roadmap/plan" className="ov-link">Open roadmap →</Link>
            </>
          ) : (
            <div className="ov-empty">
              <p><strong>No roadmap yet.</strong> A roadmap breaks the path to your target role into phases and tasks.</p>
              <Link href="/workspace/roadmap/simulation" className="ov-link">Create roadmap →</Link>
            </div>
          )}
        </section>

        <section className="ov-card ov-tasks" aria-labelledby="ov-tasks-title">
          <div className="ov-card-head">
            <h2 id="ov-tasks-title">Active tasks</h2>
            {activeTasks.length > 0 && <span className="ov-count">{activeTasks.length}</span>}
          </div>
          {!roadmap ? (
            <p className="ov-muted">Tasks appear here once you create a roadmap.</p>
          ) : activeTasks.length === 0 ? (
            <p className="ov-muted">{allTasks.length ? "All roadmap tasks are done." : "This roadmap has no tasks yet."}</p>
          ) : (
            <>
              <ul className="ov-task-list">
                {activeTasks.slice(0, 5).map((task) => (
                  <li key={task.id}><span className="ov-task-box" aria-hidden="true" /><span><strong>{task.title}</strong><small>{task.phase}</small></span></li>
                ))}
              </ul>
              {activeTasks.length > 5 && <Link href="/workspace/roadmap/plan" className="ov-link">+{activeTasks.length - 5} more in the roadmap →</Link>}
            </>
          )}
        </section>
        </>}
        {/* Without the roadmap cards the left column is short, so platforms move under the calculations. */}
        {!showRoadmap && platforms}
        </div>

        <div className="ov-col">
          <MarketCard explainability={overview.explainability} role={calculations[0]?.target_role} country={calculations[0]?.country} />
          {showRoadmap && platforms}
          {RESOURCES_PANEL_ENABLED && <ResourcesPanel />}
        </div>
      </div>
    </div>
  );
}

function CalculationRow({ item }: { item: RecentCalculationSummary }) {
  const href = `/workspace/scenarios/${item.scenario_id}`;
  const hasForecast = item.projection_id != null;
  return (
    <li className="ov-calc">
      <Link href={href} className="ov-calc-main">
        <strong>{item.name}</strong>
        <span>{[item.target_role, item.country].filter(Boolean).join(" · ")} · rev. {item.revision_number}</span>
      </Link>
      {hasForecast ? (
        <dl className="ov-calc-metrics">
          <div><dt>ROI</dt><dd>{formatPercent(item.roi_percent)}</dd></div>
          <div><dt>Payback</dt><dd>{formatPayback(item.payback_months)}</dd></div>
          <div><dt>Investment</dt><dd>{formatMoney(item.total_investment, item.currency)}</dd></div>
        </dl>
      ) : (
        <p className="ov-calc-pending">No forecast yet. <Link href={href}>View scenario</Link></p>
      )}
    </li>
  );
}
