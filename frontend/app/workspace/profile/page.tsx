"use client";

import Link from "next/link";
import { FormEvent, KeyboardEvent, useEffect, useState } from "react";
import "../../styles/dashboard.css";
import { WorkspaceState, workspaceFetch } from "@/lib/api/workspace";

export default function ProfilePage() {
  const [state, setState] = useState<WorkspaceState | null>(null);
  const [username, setUsername] = useState("");
  const [field, setField] = useState("Computer Science");
  const [country, setCountry] = useState("Poland");
  const [about, setAbout] = useState("");
  const [skills, setSkills] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState("");
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => { workspaceFetch<WorkspaceState>("/api/workspace").then((value) => { setState(value); setUsername(value.user.username); setField(value.profile.field_of_study); setCountry(value.profile.country); setAbout(value.profile.about); setSkills(value.profile.skills); }).catch((reason) => setError(reason.message)); }, []);
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try { const next = await workspaceFetch<WorkspaceState>("/api/workspace/profile", { method: "PATCH", body: JSON.stringify({ username, profile: { field_of_study: field, country, about, skills, career_target: state?.roadmap?.target_job || state?.profile.career_target || null } }) }); setState(next); setEditing(false); setMessage("Profile saved."); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save profile."); }
    finally { setBusy(false); }
  }
  function addSkill(event: KeyboardEvent<HTMLInputElement>) { if (event.key !== "Enter") return; event.preventDefault(); const value = skillInput.trim(); if (value && !skills.includes(value)) setSkills([...skills, value]); setSkillInput(""); }
  if (!state && !error) return <div className="dashboard-layout" style={{ paddingTop: 100 }}>Loading profile…</div>;
  if (!state) return <div className="dashboard-layout" style={{ paddingTop: 100 }}>{error}</div>;
  const initials = username.split(" ").map((part) => part[0]).join("").toUpperCase().slice(0, 2);
  const limit = 3;

  return <form className="dashboard-layout" onSubmit={save}><header className="dashboard-header"><p className="dashboard-breadcrumb">Workspace <i>/</i> Profile</p><div className="dashboard-title-row"><h1>Your profile</h1><span className="demo-pill">ACCOUNT DATA</span></div><p>Manage your information, track your progress, and tailor your experience.</p></header>{error && <div className="workspace-status is-error">{error}</div>}{message && <div className="workspace-status is-success">{message}</div>}
    <div className="profile-grid"><div className="widget widget-profile-info"><div className="pi-header"><div className="pi-user"><div className="pi-avatar">{initials}</div><div className="pi-user-info">{editing ? <input value={username} onChange={(event) => setUsername(event.target.value)} aria-label="Name"/> : <h2>{state.user.username}</h2>}<p>{state.user.email}</p></div></div>{editing ? <button className="btn-edit-profile" disabled={busy}>{busy ? "Saving…" : "Save profile"}</button> : <button type="button" className="btn-edit-profile" onClick={() => setEditing(true)}>Edit profile</button>}</div><div className="pi-divider"/><div className="pi-form-row"><div className="pi-input-group"><label>Field of study</label><select className="pi-select" value={field} disabled={!editing} onChange={(event) => setField(event.target.value)}><option>Computer Science</option><option>Data Science</option></select></div><div className="pi-input-group"><label>Country</label><select className="pi-select" value={country} disabled={!editing} onChange={(event) => setCountry(event.target.value)}><option>Poland</option><option>Ukraine</option><option>United Kingdom</option></select></div></div><div className="pi-input-group"><label>About me</label><textarea className="pi-textarea" value={about} disabled={!editing} maxLength={300} onChange={(event) => setAbout(event.target.value)} placeholder="Tell us a bit about yourself (optional)"/><span className="pi-char-count">{about.length}/300</span></div></div>
      <div><div className="widget widget-plan" style={{ marginBottom: 24 }}><div className="plan-header"><h3>Your plan</h3><span className="plan-pill">{state.user.plan} plan</span></div><p className="plan-desc">Explore Fence with up to {limit} scenario slots.</p><div className="plan-stats"><div className="plan-stat"><strong>{state.user.scenario_count} / {limit}</strong><span>Scenarios used</span></div><div className="plan-stat-divider"/><div className="plan-stat"><strong>{Math.max(0, limit - state.user.scenario_count)}</strong><span>Scenario slots remaining</span></div></div><Link href="/plans" className="btn-plan-options">View plan options</Link></div><div className="widget widget-skills"><h3>Your current skills</h3><p>Add skills to get more relevant insights and recommendations.</p><div className="skills-tags">{skills.map((skill) => <button type="button" disabled={!editing} className="skill-tag" key={skill} onClick={() => setSkills(skills.filter((item) => item !== skill))}>{skill}{editing ? " ×" : ""}</button>)}{editing && <input value={skillInput} onChange={(event) => setSkillInput(event.target.value)} onKeyDown={addSkill} placeholder="Add skill + Enter"/>}</div><div className="career-target-label">Career target</div><span className="career-target-tag">{state.roadmap?.target_job || state.profile.career_target || "Not set"}</span><div className="career-target-hint">Career target is updated after saving a roadmap.</div></div></div>
      <div className="widget widget-resume"><div className="resume-header"><h3>Resume assistant</h3><p>Turn your real education, skills and projects into a clear CV.</p></div><div className="resume-steps"><div className="resume-step"><span className="resume-step-pill">1. Add your experience</span></div><div className="resume-step-line"/><div className="resume-step"><span className="resume-step-pill">2. Improve your wording</span></div><div className="resume-step-line"/><div className="resume-step"><span className="resume-step-pill">3. Review your CV</span></div></div><div className="resume-footer"><p>The resume generation backend is not configured yet. These actions stay disabled to avoid pretending data was processed.</p><div className="resume-actions"><button type="button" className="btn-upload" disabled>Upload resume</button><button type="button" className="btn-create" disabled>Create my resume</button></div></div></div>
    </div>
  </form>;
}
