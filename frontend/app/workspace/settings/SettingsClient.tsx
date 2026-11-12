"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Icon, Topography, WorkspacePageHeader } from "../WorkspaceUI";
import PageLoading from "../PageLoading";
import { useWorkspacePreferences } from "../WorkspacePreferences";
import { WorkspaceState, workspaceFetch } from "@/lib/api/workspace";

type Preferences = WorkspaceState["preferences"];

const CURRENCIES: { value: Preferences["currency"]; label: string }[] = [
  { value: "Local", label: "Calculation currency (PLN or UAH)" },
  { value: "PLN", label: "PLN · Polish złoty" },
  { value: "UAH", label: "UAH · Ukrainian hryvnia" },
  { value: "EUR", label: "EUR · Euro" },
  { value: "USD", label: "USD · US dollar" },
  { value: "GBP", label: "GBP · Pound sterling" },
];
const THEMES: { value: Preferences["theme"]; label: string; hint: string }[] = [
  { value: "Fence default", label: "Light", hint: "Dark text on a light page" },
  { value: "Dark", label: "Dark", hint: "Light text on a dark page" },
  { value: "Monochrome", label: "Monochrome", hint: "Black and white, no colour" },
];

export default function SettingsClient() {
  const { apply, rates } = useWorkspacePreferences();
  const [state, setState] = useState<WorkspaceState | null>(null);
  const [language, setLanguage] = useState<Preferences["language"]>("English");
  const [currency, setCurrency] = useState<Preferences["currency"]>("Local");
  const [theme, setTheme] = useState<Preferences["theme"]>("Fence default");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [emailOpen, setEmailOpen] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailBusy, setEmailBusy] = useState(false);
  const [emailError, setEmailError] = useState("");

  useEffect(() => {
    workspaceFetch<WorkspaceState>("/api/workspace")
      .then((value) => { setState(value); setLanguage(value.preferences.language); setCurrency(value.preferences.currency); setTheme(value.preferences.theme); })
      .catch((reason) => setError(reason.message));
  }, []);

  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      const next = await workspaceFetch<WorkspaceState>("/api/workspace/preferences", { method: "PATCH", body: JSON.stringify({ language, currency, theme }) });
      setState(next);
      apply(next.preferences);
      setMessage("Settings saved. Amounts and theme update across your workspace.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save settings."); }
    finally { setBusy(false); }
  }

  async function changeEmail(event: FormEvent) {
    event.preventDefault(); event.stopPropagation(); setEmailBusy(true); setEmailError(""); setMessage("");
    try {
      const result = await workspaceFetch<{ email: string }>("/api/auth/change-email", { method: "POST", body: JSON.stringify({ new_email: newEmail.trim(), password }) });
      setState((current) => current ? { ...current, user: { ...current.user, email: result.email } } : current);
      setEmailOpen(false); setNewEmail(""); setPassword("");
      setMessage(`Your email is now ${result.email}. Use it the next time you sign in.`);
    } catch (reason) { setEmailError(reason instanceof Error ? reason.message : "Could not change the email."); }
    finally { setEmailBusy(false); }
  }

  const connections = state?.connections || {};

  return <main className="sketch-page">
    <WorkspacePageHeader section="Settings" title="Workspace settings" highlight="Workspace" description="How Fence looks and counts for you, your sign-in details and connected services. Your name, goal and plan live in Profile." />
    {error && <div className="workspace-status is-error">{error}</div>}{message && <div className="workspace-status is-success">{message}</div>}
    {!state && !error && <PageLoading label="Loading settings" />}
    {state && <div className="settings-grid">
      <div className="settings-column">
        <form className="sketch-card settings-panel" onSubmit={save}>
          <h2>General preferences</h2><p>Customize how Fence looks and works for you.</p>
          <label className="settings-row"><span><strong>Language</strong><span>Choose the language for the interface.</span></span>
            <select value={language} onChange={(event) => setLanguage(event.target.value as Preferences["language"])}><option>English</option><option>Українська</option></select></label>
          <label className="settings-row"><span><strong>Currency</strong><span>{currency === "Local" ? "Each calculation shows the currency of its country." : `Amounts are shown in ${currency} at the official NBP rate${rates?.effective_date ? ` of ${rates.effective_date}` : ""}. Calculations themselves stay in PLN or UAH.`}</span></span>
            <select value={currency} onChange={(event) => setCurrency(event.target.value as Preferences["currency"])}>{CURRENCIES.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>
          <div className="settings-row settings-theme-row"><span><strong>Theme</strong><span>{THEMES.find((option) => option.value === theme)?.hint}</span></span>
            <div className="settings-theme-options" role="radiogroup" aria-label="Theme">
              {THEMES.map((option) => (
                <button key={option.value} type="button" role="radio" aria-checked={theme === option.value}
                  className={`settings-theme is-${option.label.toLowerCase()} ${theme === option.value ? "is-on" : ""}`} onClick={() => setTheme(option.value)}>
                  <i aria-hidden="true" /> {option.label}
                </button>
              ))}
            </div>
          </div>
          <button disabled={busy} className="settings-save">{busy ? "Saving…" : "Save preferences"}</button>
        </form>
        <section className="sketch-card settings-panel"><h2>Sign-in and security</h2><p>The email and password you sign in with.</p>
          <div className="settings-row"><span><strong>Email address</strong><span>{state.user.email}</span></span>
            <button type="button" onClick={() => { setEmailOpen(!emailOpen); setEmailError(""); }} aria-expanded={emailOpen}>{emailOpen ? "Cancel" : "Change email"}</button></div>
          {emailOpen && <form className="settings-email-form" onSubmit={changeEmail}>
            <label><span>New email</span><input type="email" required value={newEmail} onChange={(event) => setNewEmail(event.target.value)} autoComplete="email" /></label>
            <label><span>Current password</span><input type="password" required value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" /></label>
            {emailError && <p className="settings-email-error" role="alert">{emailError}</p>}
            <button disabled={emailBusy} className="settings-save">{emailBusy ? "Saving…" : "Save new email"}</button>
          </form>}
          <div className="settings-row"><span><strong>Password</strong><span>Reset your password through the secure account flow.</span></span><Link href="/reset-password" className="settings-link-button">Change password</Link></div>
        </section>
      </div>
      <div className="settings-column">
        <section className="sketch-card sketch-card-dark settings-panel data-sources"><Topography/><h2>Connected data sources</h2><p>Connections are enabled only when their backend integration is configured.</p>
          {[["youtube", "▶", "YouTube"], ["github", "GH", "GitHub"], ["linkedin", "in", "LinkedIn"]].map(([id, logo, name]) => <div className="source-row" key={id}><span className="source-logo">{logo}</span><div><strong>{name}</strong><span>{connections[id]?.label || "Not configured"}</span></div><button type="button" disabled title="Connection endpoint is not configured">{connections[id]?.connected ? "Connected" : "Unavailable"}</button><Icon name="arrow" size={17}/></div>)}
        </section>
        <aside className="sketch-card sketch-card-violet settings-note"><Icon name="info" size={28}/><div><strong>Your data stays in your control</strong>Fence stores only the preferences shown here. External accounts are not contacted until an integration is configured.</div></aside>
      </div>
    </div>}
  </main>;
}
