"use client";

import { ChangeEvent, useEffect, useState } from "react";
import { workspaceFetch } from "@/lib/api/workspace";

type Check = { key: string; label: string; points: number; max: number; passed: boolean; tip: string | null };
type Review = { score: number; max_score: number; word_count: number; checks: Check[]; notes: string[]; method: string; ai: { status: string; suggestions: string[] } };
type Draft = { name: string; headline: string; email: string; phone: string; location: string; links: string; summary: string; experience: string; education: string; skills: string; projects: string; consent: boolean };

const DRAFT_KEY = "fence.cv-draft";
const escape = (value: string) => value.replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]!);
const blocks = (value: string) => value.split(/\n\s*\n/).map((block) => block.trim()).filter(Boolean);

function cvHtml(draft: Draft, country: string) {
  const section = (title: string, body: string) => body.trim() ? `<section><h2>${title}</h2>${body}</section>` : "";
  const entries = (value: string) => blocks(value).map((block) => {
    const [head, ...rest] = block.split("\n");
    return `<div class="entry"><h3>${escape(head)}</h3>${rest.length ? `<ul>${rest.map((line) => `<li>${escape(line.replace(/^[-•*]\s*/, ""))}</li>`).join("")}</ul>` : ""}</div>`;
  }).join("");
  const contact = [draft.email, draft.phone, draft.location, ...draft.links.split(/[\n,]/)].map((item) => item.trim()).filter(Boolean).map(escape).join(" · ");
  const consent = draft.consent && country === "Poland"
    ? `<p class="consent">Wyrażam zgodę na przetwarzanie moich danych osobowych dla potrzeb niezbędnych do realizacji procesu rekrutacji zgodnie z RODO (Rozporządzenie UE 2016/679).</p>` : "";
  return `<!doctype html><html><head><meta charset="utf-8"><title>${escape(draft.name || "CV")}</title><style>
    body{font-family:Arial,Helvetica,sans-serif;color:#171819;margin:36px 44px;line-height:1.4;font-size:12px}
    h1{font-size:26px;margin:0}.headline{font-size:14px;margin:2px 0 6px;color:#444}.contact{font-size:11px;color:#444;margin-bottom:14px}
    h2{font-size:13px;text-transform:uppercase;letter-spacing:.08em;border-bottom:2px solid #b7ff2a;padding-bottom:3px;margin:16px 0 6px}
    h3{font-size:12px;margin:8px 0 2px}ul{margin:2px 0 0 16px;padding:0}li{margin:1px 0}.skills{margin:0}.consent{margin-top:22px;font-size:9px;color:#555}
    @page{margin:14mm}</style></head><body>
    <h1>${escape(draft.name)}</h1>${draft.headline ? `<p class="headline">${escape(draft.headline)}</p>` : ""}<p class="contact">${contact}</p>
    ${section("Profile", draft.summary ? `<p>${escape(draft.summary)}</p>` : "")}
    ${section("Experience", entries(draft.experience))}
    ${section("Education", entries(draft.education))}
    ${section("Skills", draft.skills ? `<p class="skills">${escape(draft.skills)}</p>` : "")}
    ${section("Projects", entries(draft.projects))}
    ${consent}</body></html>`;
}

/** Upload a CV for a rubric check, or build one here and save it as PDF. */
export default function ResumeAssistant({ name, email, target, country }: { name: string; email: string; target: string; country: string }) {
  const [review, setReview] = useState<Review | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [building, setBuilding] = useState(false);
  const [draft, setDraft] = useState<Draft>({ name, headline: target, email, phone: "", location: "", links: "", summary: "", experience: "", education: "", skills: "", projects: "", consent: country === "Poland" });

  useEffect(() => {
    try { const saved = window.localStorage.getItem(DRAFT_KEY); if (saved) setDraft((current) => ({ ...current, ...JSON.parse(saved) })); } catch { /* drafts are a convenience */ }
  }, []);
  useEffect(() => {
    try { window.localStorage.setItem(DRAFT_KEY, JSON.stringify(draft)); } catch { /* not saved in this browser */ }
  }, [draft]);

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setBusy(true); setError(""); setReview(null);
    try {
      const body = new FormData();
      body.append("file", file);
      setReview(await workspaceFetch<Review>("/api/workspace/resume/review", { method: "POST", body }));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Fence could not check this file."); }
    finally { setBusy(false); }
  }

  function savePdf() {
    const view = window.open("", "_blank", "width=900,height=1100");
    if (!view) { setError("Allow pop-ups for Fence to save the CV as PDF."); return; }
    view.document.write(cvHtml(draft, country));
    view.document.close();
    view.focus();
    // document.write pages have no reliable load event; print once the layout has settled.
    window.setTimeout(() => view.print(), 400);
  }

  const field = (key: keyof Draft, label: string, rows = 0, placeholder = "") => (
    <label className="cv-field"><span>{label}</span>
      {rows ? <textarea rows={rows} value={draft[key] as string} placeholder={placeholder} onChange={(event) => setDraft({ ...draft, [key]: event.target.value })} />
        : <input value={draft[key] as string} placeholder={placeholder} onChange={(event) => setDraft({ ...draft, [key]: event.target.value })} />}
    </label>
  );

  return (
    <div className="widget widget-resume">
      <div className="resume-header"><h3>Resume assistant</h3><p>Check your CV against what recruiters and applicant-tracking systems look for, or build one here.</p></div>
      <div className="resume-actions">
        <label className={`btn-upload ${busy ? "is-busy" : ""}`}>
          <input type="file" accept=".pdf,.docx,.txt" onChange={upload} disabled={busy} hidden />
          {busy ? "Checking…" : "Upload and check CV"}
        </label>
        <button type="button" className="btn-create" onClick={() => setBuilding(!building)} aria-expanded={building}>{building ? "Close the builder" : "Create my CV"}</button>
      </div>
      <p className="resume-privacy">PDF, DOCX or TXT up to 2 MB. The file is read once to check it and is not stored.</p>
      {error && <p className="resume-error" role="alert">{error}</p>}

      {review && <div className="resume-review" aria-live="polite">
        <div className="resume-score"><strong>{review.score}<small>/{review.max_score}</small></strong><span>{review.score >= 80 ? "Strong CV" : review.score >= 55 ? "Good base, a few gaps" : "Needs work before you apply"}</span></div>
        <ul className="resume-checks">{review.checks.map((check) => (
          <li key={check.key} className={check.passed ? "is-ok" : ""}><b>{check.passed ? "✓" : "!"}</b><span>{check.label}{check.tip ? <small>{check.tip}</small> : null}</span><em>{check.points}/{check.max}</em></li>
        ))}</ul>
        {review.notes.map((note) => <p key={note} className="resume-note">{note}</p>)}
        {review.ai.status === "ok" && review.ai.suggestions.length ? <div className="resume-ai"><h4>AI suggestions <small>written by an AI model, not part of the score</small></h4><ul>{review.ai.suggestions.map((item) => <li key={item}>{item}</li>)}</ul></div>
          : <p className="resume-method">AI suggestions: {review.ai.status === "not_configured" ? "not configured on this server." : "not available right now."}</p>}
        <p className="resume-method">{review.method}</p>
      </div>}

      {building && <div className="cv-builder">
        <div className="cv-form">
          {field("name", "Full name")}{field("headline", "Title", 0, "e.g. Junior Python Developer")}
          {field("email", "Email")}{field("phone", "Phone", 0, "+48 …")}{field("location", "City")}{field("links", "Links", 0, "LinkedIn, GitHub, portfolio")}
          {field("summary", "Profile", 3, "Two or three lines about what you do and what you want next")}
          {field("experience", "Experience", 6, "Job title, Company (2022 – 2024)\n- Built …\n- Reduced … by 30%\n\nNext job …")}
          {field("education", "Education", 4, "BSc Computer Science, University (2019 – 2023)")}
          {field("skills", "Skills", 2, "Python, SQL, Docker …")}
          {field("projects", "Projects", 4, "Project name\n- What it does, with a number")}
          {country === "Poland" && <label className="cv-consent"><input type="checkbox" checked={draft.consent} onChange={(event) => setDraft({ ...draft, consent: event.target.checked })} /> Add the RODO consent clause (expected by employers in Poland)</label>}
          <button type="button" className="btn-create" onClick={savePdf}>Save as PDF</button>
          <p className="resume-privacy">The draft stays in this browser only. “Save as PDF” opens your browser&apos;s print window: choose “Save as PDF”.</p>
        </div>
        <iframe className="cv-preview" title="CV preview" srcDoc={cvHtml(draft, country)} />
      </div>}
    </div>
  );
}
