"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Icon, Topography, WorkspacePageHeader } from "../../WorkspaceUI";
import { RoadmapPlan, RoadmapTask, WorkspaceState, workspaceFetch } from "@/lib/api/workspace";

export default function PlanClient() {
  const [state, setState] = useState<WorkspaceState | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [busyId, setBusyId] = useState("");
  const [error, setError] = useState("");

  useEffect(() => { workspaceFetch<WorkspaceState>("/api/workspace").then((value) => { setState(value); setSelectedId(value.roadmap?.plan.phases.flatMap((phase) => phase.tasks || []).find((task) => !task.completed)?.id || ""); }).catch((reason) => setError(reason.message)); }, []);
  const tasks = useMemo(() => state?.roadmap?.plan.phases.flatMap((phase) => phase.tasks || []) || [], [state]);
  const selected = tasks.find((task) => task.id === selectedId) || tasks[0];
  const completed = tasks.filter((task) => task.completed).length;
  const percent = tasks.length ? Math.round(completed / tasks.length * 100) : 0;

  async function toggleTask(task: RoadmapTask) {
    if (!state?.roadmap) return;
    setBusyId(task.id); setError("");
    try {
      const response = await workspaceFetch<{ id: number; target_job: string; plan: RoadmapPlan }>(`/api/workspace/roadmaps/${state.roadmap.id}/tasks/${task.id}`, { method: "PATCH", body: JSON.stringify({ completed: !task.completed }) });
      setState({ ...state, roadmap: { ...state.roadmap, plan: response.plan } });
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not update the task."); }
    finally { setBusyId(""); }
  }

  if (!state && !error) return <main className="sketch-page"><WorkspacePageHeader section="Roadmap / My plan" title="Your career roadmap" highlight="roadmap" description="Step by step from learning to real opportunities." /><div className="workspace-status">Loading your roadmap…</div></main>;
  if (error && !state) return <main className="sketch-page"><WorkspacePageHeader section="Roadmap / My plan" title="Your career roadmap" highlight="roadmap" description="Step by step from learning to real opportunities." /><div className="workspace-status is-error">{error}</div></main>;
  if (!state?.roadmap) return <main className="sketch-page"><WorkspacePageHeader section="Roadmap / My plan" title="Your career roadmap" highlight="roadmap" description="Step by step from learning to real opportunities." /><article className="sketch-card sketch-card-violet empty-roadmap"><h2>No roadmap yet</h2><p>Run a simulation and save the result to create your plan.</p><Link href="/workspace/roadmap/simulation" className="sketch-btn sketch-btn-primary"><Icon name="map" /> Create roadmap</Link></article></main>;

  return <main className="sketch-page">
    <WorkspacePageHeader section="Roadmap / My plan" title="Your career roadmap" highlight="roadmap" description={`Your path to ${state.roadmap.target_job}.`} />
    {error && <div className="workspace-status is-error">{error}</div>}
    <article className="sketch-card progress-card"><h2>Your progress</h2><div className="progress-meter"><span>{completed} of {tasks.length} tasks completed</span><strong>{percent}%</strong><i><b style={{ width: `${percent}%` }} /></i></div><div className="progress-quote">Small steps today.<br />A bigger tomorrow.</div></article>
    <section className="phases-row" aria-label="Roadmap phases">{state.roadmap.plan.phases.map((phase, index) => { const phaseTasks = phase.tasks || []; const phaseDone = phaseTasks.length > 0 && phaseTasks.every((task) => task.completed); return <article className={`sketch-card phase-card ${phaseDone ? "is-complete" : ""}`} key={phase.id}><span className="phase-dot">{phaseDone && <Icon name="check" />}</span><div><h3>{index + 1}. {phase.title}</h3><p>{phase.hours} hours · {phase.weeks} weeks</p></div><span className={`sketch-chip ${phaseDone ? "" : "is-active"}`}>{phaseDone ? "Completed" : "In progress"}</span></article>; })}</section>
    <div className="plan-grid"><article className="sketch-card task-list-card"><div className="task-card-head"><h2 className="sketch-section-title">Tasks in this plan</h2><span className="sketch-muted">{tasks.length} tasks</span></div>{tasks.map((task, index) => <button type="button" className={`task-row ${selected?.id === task.id ? "is-selected" : ""}`} key={task.id} onClick={() => setSelectedId(task.id)}><i className={`task-state ${task.completed ? "is-done" : ""}`}>{task.completed ? "✓" : ""}</i><b>{index + 1}.</b><div><strong>{task.title}</strong><span>{task.description}</span></div><Icon name="arrow" size={17}/></button>)}<Link href="/workspace/courses" className="find-courses-row"><Icon name="search" size={28}/><div><strong>Find relevant courses</strong><p>Search for courses, tutorials and learning materials.</p></div><Icon name="arrow" /></Link></article>
      {selected && <article className="sketch-card sketch-card-dark task-detail-card"><Topography /><div className="task-detail-top"><div><span className="sketch-chip is-active">{selected.completed ? "Completed" : "In progress"}</span><h2>{selected.title}</h2><p>{selected.description}</p></div><button type="button" disabled={busyId === selected.id} onClick={() => toggleTask(selected)} className="sketch-btn sketch-btn-primary"><Icon name="check" /> {busyId === selected.id ? "Saving…" : selected.completed ? "Mark as active" : "Mark as complete"}</button></div><div className="task-tabs"><span className="is-active">Overview</span><Link href="/workspace/courses">Resources</Link></div><h3>Recommended resources</h3><div className="resource-list"><Link href="/workspace/courses" className="dark-resource"><Icon name="book"/><div><strong>Find a course for this task</strong><span>Browse the server-backed Fence learning catalog.</span></div><Icon name="arrow" size={17}/></Link></div><h3>Skills</h3><div className="phase-skills">{state.roadmap.plan.phases.find((phase) => (phase.tasks || []).some((task) => task.id === selected.id))?.skills.map((skill) => <span className="sketch-chip" key={skill}>{skill}</span>)}</div></article>}
    </div>
  </main>;
}
