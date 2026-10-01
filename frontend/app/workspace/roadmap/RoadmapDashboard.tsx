"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Icon, Topography, WorkspacePageHeader } from "../WorkspaceUI";
import { WorkspaceState, workspaceFetch } from "../workspaceApi";

export default function RoadmapDashboard() {
  const [state, setState] = useState<WorkspaceState | null>(null);
  const [error, setError] = useState("");

  useEffect(() => { workspaceFetch<WorkspaceState>("/api/workspace").then(setState).catch((reason) => setError(reason.message)); }, []);
  const progress = useMemo(() => {
    const phases = state?.roadmap?.plan.phases || [];
    const tasks = phases.flatMap((phase) => phase.tasks || []);
    return { completed: tasks.filter((task) => task.completed).length, total: tasks.length, hours: phases.reduce((sum, phase) => sum + phase.hours, 0), phase: phases.find((phase) => (phase.tasks || []).some((task) => !task.completed))?.title || phases.at(-1)?.title || "—" };
  }, [state]);

  return <main className="sketch-page">
    <WorkspacePageHeader section="Roadmap / Dashboard" title="Your career workspace" highlight="career workspace" description="Your plan, skills and next steps in one place." />
    {error && <div className="workspace-status is-error">{error}</div>}
    {!state && !error && <div className="workspace-status">Loading your workspace…</div>}
    {state && <div className="roadmap-dashboard-grid">
      <div>
        <article className="sketch-card sketch-card-dark faculty-card"><Topography /><small>Your faculty</small><h2>{state.profile.field_of_study}</h2><p>{state.profile.country}</p><p className="faculty-copy">Explore career paths, key skills and practical resources to make the most of your studies.</p><div className="faculty-meta"><div><span>Field</span><strong>{state.profile.field_of_study}</strong></div><div><span>Country</span><strong>{state.profile.country}</strong></div><div><span>Skills</span><strong>{state.profile.skills.length || "—"}</strong></div></div></article>
        <article className="sketch-card sketch-card-violet empty-roadmap"><div className="empty-roadmap-head"><span className="empty-roadmap-icon"><Icon name="target" size={34} /></span><div><h2>{state.roadmap ? state.roadmap.target_job : "No roadmap yet"}</h2><p>{state.roadmap ? "Your personalised learning path is ready." : "Create a roadmap to personalize these materials to a career goal."}</p><Link href={state.roadmap ? "/workspace/roadmap/plan" : "/workspace/roadmap/simulation"} className="sketch-btn sketch-btn-primary"><Icon name="map" /> {state.roadmap ? "Open roadmap" : "Create roadmap"}</Link></div></div><ul><li>Get relevant content for your career goal</li><li>See recommended skills and next steps</li><li>Build a personalised learning path</li></ul></article>
      </div>
      <div className="roadmap-main">
        <article className="sketch-card sketch-card-dark learning-plan-card"><Topography /><small>Your learning plan</small><h2>{state.roadmap ? state.roadmap.target_job : "Start your first roadmap"}</h2><p>{state.roadmap ? `${state.roadmap.plan.weeks} weeks at ${state.roadmap.plan.hours_per_week} hours per week.` : "Choose a career goal and use your existing skills to build a plan."}</p><Link href={state.roadmap ? "/workspace/roadmap/plan" : "/workspace/roadmap/simulation"} className="sketch-btn sketch-btn-primary"><Icon name="map" /> {state.roadmap ? "Continue roadmap" : "Create roadmap"}</Link><div className="learning-stats"><div><Icon name="check" /><span>Tasks completed<strong>{progress.total ? `${progress.completed}/${progress.total}` : "—"}</strong></span></div><div><Icon name="clock" /><span>Learning hours<strong>{progress.hours || "—"}</strong></span></div><div><Icon name="tasks" /><span>Current phase<strong>{progress.phase}</strong></span></div></div></article>
        <div className="roadmap-mini-grid"><article className="sketch-card roadmap-mini"><h3>Skills overview</h3><span className="mini-icon"><Icon name="book" size={29} /></span><p>{state.profile.skills.length ? state.profile.skills.join(" · ") : "Add your current skills to identify what to learn next."}</p><Link href="/workspace/profile" className="sketch-chip is-active">Edit skills</Link></article><article className="sketch-card roadmap-mini"><h3>Next tasks</h3><span className="mini-icon"><Icon name="tasks" size={29} /></span><p>{progress.total ? `${progress.total - progress.completed} tasks remain in your plan.` : "Your upcoming tasks will appear after creating a roadmap."}</p>{state.roadmap ? <Link href="/workspace/roadmap/plan" className="sketch-chip">Open my plan ↗</Link> : <span className="sketch-chip">Not created</span>}</article></div>
        <article className="sketch-card simulation-strip"><span className="mini-icon"><Icon name="laptop" /></span><div><h3>Simulations</h3><p>Explore a career goal and estimate your learning effort.</p></div><span className="sketch-muted">{state.user.scenario_count} saved</span><Link href="/workspace/roadmap/simulation" className="sketch-btn">New simulation <Icon name="arrow" size={17} /></Link></article>
        <article className="sketch-card resource-card"><div className="resource-head"><div><h2 className="sketch-section-title">Helpful resources</h2><span className="sketch-muted">Courses are loaded from the Fence catalog.</span></div></div><Link href="/workspace/courses" className="resource-row"><Icon name="book" /><div><strong>Explore recommended courses</strong><span>Filter learning materials by topic, level and format.</span></div><Icon name="arrow" size={17} /></Link></article>
      </div>
    </div>}
  </main>;
}
