"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import "../../styles/dashboard.css";
import PageLoading from "../PageLoading";
import ResumeAssistant from "./ResumeAssistant";
import { WorkspaceState, workspaceFetch } from "@/lib/api/workspace";
import type { SimulationScenarioListItem } from "@/lib/api/generated";

// The field of study follows the goal: the programme of the latest calculation, else the career's usual field.
const CAREER_FIELD: Record<string, string> = {
  "frontend developer": "Computer Science", "java developer": "Computer Science", "python backend developer": "Computer Science",
  "qa engineer": "Computer Science", ".net developer": "Computer Science", "data analyst": "Data Science and Statistics",
  accountant: "Finance and Accounting", lawyer: "Law", doctor: "Medicine", nurse: "Nursing", pharmacist: "Pharmacy",
  psychologist: "Psychology", teacher: "Education", "civil engineer": "Civil Engineering", "marketing specialist": "Marketing and Management",
};

export default function ProfilePage() {
  const [state, setState] = useState<WorkspaceState | null>(null);
  const [latest, setLatest] = useState<SimulationScenarioListItem | null>(null);
  const [username, setUsername] = useState("");
  const [country, setCountry] = useState("Poland");
  const [about, setAbout] = useState("");
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    workspaceFetch<WorkspaceState>("/api/workspace")
      .then((value) => { setState(value); setUsername(value.user.username); setCountry(value.profile.country); setAbout(value.profile.about); })
      .catch((reason) => setError(reason.message));
    workspaceFetch<SimulationScenarioListItem[]>("/api/simulations").then((items) => setLatest(items[0] ?? null)).catch(() => setLatest(null));
  }, []);

  const goal = state?.roadmap?.target_job || state?.profile.career_target || latest?.target_role || "";
  const field = latest?.specialization || CAREER_FIELD[goal.trim().toLowerCase()] || (goal ? "" : "");

  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      const next = await workspaceFetch<WorkspaceState>("/api/workspace/profile", { method: "PATCH", body: JSON.stringify({ username, profile: { field_of_study: field || state?.profile.field_of_study || "Not chosen", country, about, skills: state?.profile.skills ?? [], career_target: goal || null } }) });
      setState(next); setEditing(false); setMessage("Profile saved.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save profile."); }
    finally { setBusy(false); }
  }

  if (!state && !error) return <PageLoading label="Loading your profile" />;
  if (!state) return <div className="dashboard-layout" style={{ paddingTop: 100 }}>{error}</div>;
  const initials = username.split(" ").map((part) => part[0]).join("").toUpperCase().slice(0, 2);
  const used = state.user.scenario_count;
  const limit = state.user.scenario_limit ?? null;
  const left = limit == null ? null : Math.max(0, limit - used);
  const over = limit != null && used > limit;

  return <div className="dashboard-layout">
    <header className="dashboard-header"><p className="dashboard-breadcrumb">Workspace <i>/</i> Profile</p><div className="dashboard-title-row"><h1>Your profile</h1><span className="demo-pill">ACCOUNT DATA</span></div>
      <p>Who you are, your goal and your plan. Theme, currency, email and password are in <Link href="/workspace/settings">Settings</Link>.</p></header>
    {error && <div className="workspace-status is-error">{error}</div>}{message && <div className="workspace-status is-success">{message}</div>}
    <div className="profile-grid">
      <form className="widget widget-profile-info" onSubmit={save}>
        <div className="pi-header"><div className="pi-user"><div className="pi-avatar">{initials}</div><div className="pi-user-info">{editing ? <input value={username} onChange={(event) => setUsername(event.target.value)} aria-label="Name"/> : <h2>{state.user.username}</h2>}<p>{state.user.email}</p></div></div>
          {editing ? <button className="btn-edit-profile" disabled={busy}>{busy ? "Saving…" : "Save profile"}</button> : <button type="button" className="btn-edit-profile" onClick={() => setEditing(true)}>Edit profile</button>}</div>
        <div className="pi-divider"/>
        <div className="pi-form-row">
          <div className="pi-input-group"><label>Field of study</label><div className="pi-readonly">{field || "Chosen with your goal"}</div><small className="pi-hint">{latest?.specialization ? "From the programme of your latest calculation." : goal ? `The usual field for ${goal}.` : "Make a calculation and the field follows from its programme."}</small></div>
          <div className="pi-input-group"><label>Country</label><select className="pi-select" value={country} disabled={!editing} onChange={(event) => setCountry(event.target.value)}><option>Poland</option><option>Ukraine</option></select></div>
        </div>
        <div className="pi-input-group"><label>About me</label><textarea className="pi-textarea" value={about} disabled={!editing} maxLength={300} onChange={(event) => setAbout(event.target.value)} placeholder="Tell us a bit about yourself (optional)"/><span className="pi-char-count">{about.length}/300</span></div>
      </form>
      <div>
        <div className="widget widget-plan" style={{ marginBottom: 24 }}>
          <div className="plan-header"><h3>Your plan</h3><span className="plan-pill">{state.user.plan} plan</span></div>
          <p className="plan-desc">{limit == null ? "Your plan has no limit on saved calculations." : `Your plan includes ${limit} saved calculations. Each calculation you save uses one.`}</p>
          <div className="plan-stats">
            <div className="plan-stat"><strong className={over || left === 0 ? "is-full" : ""}>{used}{limit != null ? ` / ${limit}` : ""}</strong><span>Calculations saved</span></div>
            <div className="plan-stat-divider"/>
            <div className="plan-stat"><strong>{left ?? "∞"}</strong><span>Calculations left</span></div>
          </div>
          {limit != null && left === 0 ? <p className="plan-warning">{over ? `You have ${used - limit} more than your plan allows from before the limit was enforced. They stay readable, but` : "All calculations are used:"} new calculations are blocked until you delete some in <Link href="/workspace/scenarios">Saved Scenarios</Link> or upgrade.</p> : null}
          <Link href="/pricing" className="btn-plan-options">View plan options</Link>
        </div>
        <div className="widget widget-skills">
          <h3>Your skills</h3>
          <p>Skills will fill in automatically from your DreamWork progress once that service is connected. Until then there is nothing to type here.</p>
          <div className="career-target-label">Career target</div>
          <span className="career-target-tag">{goal || "Not set"}</span>
          <div className="career-target-hint">Comes from your roadmap or your latest calculation.</div>
        </div>
      </div>
      <ResumeAssistant name={state.user.username} email={state.user.email} target={goal} country={country} />
    </div>
  </div>;
}
