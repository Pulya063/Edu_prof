"use client";

import Link from "next/link";
import { FormEvent, KeyboardEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Icon, Topography, WorkspacePageHeader } from "../../WorkspaceUI";
import { RoadmapPlan, WorkspaceState, workspaceFetch } from "../../workspaceApi";

const roles = ["Junior Python Developer", "Data Analyst", "Frontend Developer"];

export default function SimulationClient() {
  const router = useRouter();
  const [targetJob, setTargetJob] = useState(roles[0]);
  const [level, setLevel] = useState("Beginner");
  const [hours, setHours] = useState(8);
  const [skills, setSkills] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState("");
  const [plan, setPlan] = useState<RoadmapPlan | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { workspaceFetch<WorkspaceState>("/api/workspace").then((state) => { setSkills(state.profile.skills); if (state.profile.career_target) setTargetJob(state.profile.career_target); }).catch(() => undefined); }, []);

  async function updateSimulation(event?: FormEvent) {
    event?.preventDefault(); setBusy(true); setError("");
    try { setPlan(await workspaceFetch<RoadmapPlan>("/api/workspace/roadmap/preview", { method: "POST", body: JSON.stringify({ target_job: targetJob, current_level: level, hours_per_week: hours, skills }) })); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not calculate the plan."); }
    finally { setBusy(false); }
  }

  async function saveRoadmap() {
    setBusy(true); setError("");
    try { await workspaceFetch("/api/roadmap/generate", { method: "POST", body: JSON.stringify({ target_job: targetJob, hours_per_week: hours, current_income: 0, skills }) }); router.push("/workspace/roadmap/plan"); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save the roadmap."); setBusy(false); }
  }

  function addSkill(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key !== "Enter") return;
    event.preventDefault();
    const value = skillInput.trim();
    if (value && !skills.includes(value)) setSkills([...skills, value]);
    setSkillInput("");
  }

  const shownPlan = plan || { target_job: targetJob, current_level: level, hours_per_week: hours, skills, total_hours: 240, weeks: 30, phases: [{ id: "foundations", title: "Foundations", hours: 80, weeks: 10, skills: ["Python", "Data structures", "Problem solving"] }, { id: "backend", title: "Backend development", hours: 100, weeks: 13, skills: ["APIs", "FastAPI", "Databases", "SQL", "Testing"] }, { id: "career", title: "Projects & career prep", hours: 60, weeks: 8, skills: ["Project development", "Deployment", "Git workflow"] }] };

  return <main className="sketch-page">
    <WorkspacePageHeader section="Roadmap / Simulation" title="Plan your next career move" highlight="next career move" description="See a personalized learning plan based on your goals, skills and available time." />
    {error && <div className="workspace-status is-error">{error}</div>}
    <div className="simulation-top">
      <form className="sketch-card simulation-form" onSubmit={updateSimulation}><h2>Your simulation settings</h2><p>Tell us your goal and background. We&apos;ll calculate a personalized learning plan on the server.</p><label>Target role<select value={targetJob} onChange={(event) => setTargetJob(event.target.value)}>{roles.map((role) => <option key={role}>{role}</option>)}</select></label><div className="simulation-inline"><label>Current level<select value={level} onChange={(event) => setLevel(event.target.value)}><option>Beginner</option><option>Intermediate</option><option>Advanced</option></select></label><label>Hours per week<div className="hours-choice" role="group" aria-label="Hours per week">{[4, 8, 12, 16].map((value) => <button type="button" key={value} className={hours === value ? "is-active" : ""} aria-pressed={hours === value} onClick={() => setHours(value)}>{value}</button>)}</div></label></div><label>Current skills<div className="skill-entry">{skills.map((skill) => <button type="button" className="sketch-chip" key={skill} onClick={() => setSkills(skills.filter((item) => item !== skill))}>{skill} ×</button>)}<span className="sketch-field"><input value={skillInput} onChange={(event) => setSkillInput(event.target.value)} onKeyDown={addSkill} placeholder="Add a skill and press Enter" aria-label="Add a skill"/><Icon name="search" size={18}/></span></div></label><button disabled={busy} className="sketch-btn sketch-btn-primary">{busy ? "Calculating…" : "Update simulation"}</button></form>
      <article className="sketch-card sketch-card-dark estimate-card"><Topography /><h2>Your estimated plan</h2><div className="estimate-numbers"><div><strong>{shownPlan.total_hours}</strong><span>learning hours</span></div><div><strong>{shownPlan.weeks}</strong><span>weeks</span></div><div><strong>{shownPlan.hours_per_week}h</strong><span>per week</span></div></div><p>Calculated from your level, current skills and weekly availability. This is an estimate, not a guarantee.</p><small>Required skills</small><div className="skills-bars">{shownPlan.phases.map((phase) => <div className="skill-bar" key={phase.id}><strong>{phase.title}</strong><i><b style={{ width: `${Math.max(18, Math.round(phase.hours / shownPlan.total_hours * 100))}%` }} /></i><span>{phase.hours}h</span></div>)}</div></article>
    </div>
    <div className="learning-plan-title"><h2>Your learning plan</h2><p>A step-by-step path to build the skills you need.</p></div><section className="learning-phase-grid" aria-label="Learning phases">{shownPlan.phases.map((phase, index) => <article className="sketch-card learning-phase" key={phase.id}><h3>{index + 1}. {phase.title}<span className="sketch-chip is-active">{phase.weeks} weeks</span></h3><p>{phase.hours} focused learning hours.</p><div className="phase-skills"><small>Skills you&apos;ll gain</small>{phase.skills.map((skill) => <span className="sketch-chip" key={skill}>{skill}</span>)}</div></article>)}</section>
    <div className="simulation-actions"><button type="button" disabled={busy} onClick={saveRoadmap} className="sketch-btn" style={{ background: "#151819", color: "#fff" }}><Icon name="map" /> {busy ? "Saving…" : "Save as roadmap"}</button><Link href="/workspace/courses" className="sketch-btn"><Icon name="arrow" /> Find courses</Link></div>
  </main>;
}
