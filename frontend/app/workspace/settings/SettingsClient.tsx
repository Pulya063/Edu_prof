"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Icon, Topography, WorkspacePageHeader } from "../WorkspaceUI";
import { WorkspaceState, workspaceFetch } from "@/lib/api/workspace";

export default function SettingsClient() {
  const [state, setState] = useState<WorkspaceState | null>(null);
  const [language, setLanguage] = useState<WorkspaceState["preferences"]["language"]>("English");
  const [currency, setCurrency] = useState<WorkspaceState["preferences"]["currency"]>("USD");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => { workspaceFetch<WorkspaceState>("/api/workspace").then((value) => { setState(value); setLanguage(value.preferences.language); setCurrency(value.preferences.currency); }).catch((reason) => setError(reason.message)); }, []);
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try { const next = await workspaceFetch<WorkspaceState>("/api/workspace/preferences", { method: "PATCH", body: JSON.stringify({ language, currency, theme: "Fence default" }) }); setState(next); setMessage("Settings saved to your account."); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save settings."); }
    finally { setBusy(false); }
  }
  const connections = state?.connections || {};

  return <main className="sketch-page">
    <WorkspacePageHeader section="Settings" title="Workspace settings" highlight="Workspace" description="Personalize your experience and manage your data, privacy and security." />
    {error && <div className="workspace-status is-error">{error}</div>}{message && <div className="workspace-status is-success">{message}</div>}
    {!state && !error && <div className="workspace-status">Loading settings…</div>}
    {state && <form className="settings-grid" onSubmit={save}><div className="settings-column"><section className="sketch-card settings-panel"><h2>General preferences</h2><p>Customize how Fence looks and works for you.</p><label className="settings-row"><span><strong>Language</strong><span>Choose the language for the interface.</span></span><select value={language} onChange={(event) => setLanguage(event.target.value as typeof language)}><option>English</option><option>Українська</option></select></label><label className="settings-row"><span><strong>Currency</strong><span>Set your preferred currency for costs and calculations.</span></span><select value={currency} onChange={(event) => setCurrency(event.target.value as typeof currency)}><option value="USD">USD (US Dollar)</option><option value="EUR">EUR (Euro)</option><option value="PLN">PLN (Polish Złoty)</option><option value="GBP">GBP (Pound Sterling)</option></select></label><label className="settings-row"><span><strong>Theme</strong><span>Choose your visual theme.</span></span><select value="Fence default" disabled><option>Fence default</option></select></label></section><section className="sketch-card settings-panel"><h2>Security</h2><p>Security actions remain managed by the existing account service.</p><div className="settings-row"><span><strong>Email address</strong><span>{state.user.email}</span></span><button type="button" disabled title="Email change is not available yet">Change email</button></div><div className="settings-row"><span><strong>Password</strong><span>Reset your password through the secure account flow.</span></span><Link href="/reset-password" className="settings-link-button">Change password</Link></div><div className="settings-row"><span><strong>Active sessions</strong><span>Session management is not available yet.</span></span><button type="button" disabled>Manage sessions</button></div></section></div>
      <div className="settings-column"><section className="sketch-card sketch-card-dark settings-panel data-sources"><Topography/><h2>Connected data sources</h2><p>Connections are enabled only when their backend integration is configured.</p>{[["youtube", "▶", "YouTube"], ["github", "GH", "GitHub"], ["linkedin", "in", "LinkedIn"]].map(([id, logo, name]) => <div className="source-row" key={id}><span className="source-logo">{logo}</span><div><strong>{name}</strong><span>{connections[id]?.label || "Not configured"}</span></div><button type="button" disabled title="Connection endpoint is not configured">{connections[id]?.connected ? "Connected" : "Unavailable"}</button><Icon name="arrow" size={17}/></div>)}</section><aside className="sketch-card sketch-card-violet settings-note"><Icon name="info" size={28}/><div><strong>Your data stays in your control</strong>Fence stores only the preferences shown here. External accounts are not contacted until an integration is configured.</div></aside><button disabled={busy} className="settings-save">{busy ? "Saving…" : "Save changes"}</button><p className="settings-save-note">Preferences are persisted by the Fence backend.</p></div></form>}
  </main>;
}
