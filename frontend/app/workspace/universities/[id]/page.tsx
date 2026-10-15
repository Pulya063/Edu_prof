"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Icon, Topography, WorkspacePageHeader } from "../../WorkspaceUI";
import { WorkspaceUniversityDetails, workspaceFetch } from "@/lib/api/workspace";

export default function UniversityDetailsPage() {
  const params = useParams<{ id: string }>();
  const [university, setUniversity] = useState<WorkspaceUniversityDetails | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    workspaceFetch<WorkspaceUniversityDetails>(`/api/workspace/universities/${encodeURIComponent(params.id)}`)
      .then(setUniversity)
      .catch((reason) => setError(reason.message));
  }, [params.id]);

  if (!university) return <main className="sketch-page"><WorkspacePageHeader section="Compare / University details" title="University details" highlight="details" description="Programme, cost and application information in one place." />{error ? <div className="workspace-status is-error">{error}</div> : <div className="workspace-status">Loading university details…</div>}</main>;

  const total = university.annual_tuition && university.duration_years ? university.annual_tuition * university.duration_years : null;
  const money = (value: number | null) => value == null ? "—" : new Intl.NumberFormat("en", { style: "currency", currency: university.currency, maximumFractionDigits: 0 }).format(value);

  return <main className="sketch-page university-full-page">
    <WorkspacePageHeader section="Compare / University details" title={university.name} highlight={university.name} description={`${university.program_name} · ${university.city || university.country}, ${university.country}`} />
    <Link href="/workspace/compare" className="university-back">← Back to comparison</Link>
    <section className="sketch-card sketch-card-dark university-full-hero"><Topography/><div><span className="sketch-chip is-active">{university.data_quality === "database" ? "Fence database" : "Illustrative data"}</span><h2>{university.program_name}</h2><p>{university.description}</p></div>{university.website ? <a href={university.website} target="_blank" rel="noreferrer" className="sketch-btn sketch-btn-primary">Official university website <Icon name="arrow" size={17}/></a> : <button type="button" className="sketch-btn" disabled>Official website unavailable</button>}<div className="university-full-metrics"><div><span>Annual tuition</span><strong>{money(university.annual_tuition)}</strong></div><div><span>Duration</span><strong>{university.duration_years ? `${university.duration_years} years` : "—"}</strong></div><div><span>Estimated tuition total</span><strong>{money(total)}</strong></div><div><span>Study mode</span><strong>{university.study_mode}</strong></div></div></section>
    <div className="university-full-grid"><section className="sketch-card university-info-panel"><div className="university-panel-title"><Icon name="book"/><div><h2>Programmes</h2><p>Study options stored for this university.</p></div></div>{university.programmes.length ? <div className="university-detail-list">{university.programmes.map((programme) => <article key={programme.id}><div><h3>{programme.name}</h3><p>{programme.description || "No programme description is stored."}</p></div><div className="university-list-meta"><span>{programme.duration_years} years</span><strong>{money(programme.tuition_cost)} / year</strong></div></article>)}</div> : <div className="university-empty">No programme records are available yet.</div>}</section>
      <section className="sketch-card university-info-panel"><div className="university-panel-title"><Icon name="document"/><div><h2>Admissions & documents</h2><p>Official resources connected to the university record.</p></div></div>{university.documents.length ? <div className="university-detail-list">{university.documents.map((document) => <a href={document.source_url} target="_blank" rel="noreferrer" key={document.id}><div><h3>{document.title}</h3><p>{document.subject_name}</p></div><Icon name="arrow" size={17}/></a>)}</div> : <div className="university-empty">No verified admission documents are stored. Use the official university website for current requirements.</div>}</section>
      <section className="sketch-card university-info-panel"><div className="university-panel-title"><Icon name="graduation"/><div><h2>Scholarships</h2><p>Funding opportunities attached to this university.</p></div></div>{university.scholarships.length ? <div className="university-detail-list">{university.scholarships.map((scholarship) => <article key={scholarship.id}><div><h3>{scholarship.name}</h3><p>{scholarship.description || scholarship.eligibility || "See the official source for eligibility."}</p></div><div className="university-list-meta">{scholarship.amount != null && <strong>{scholarship.currency || university.currency} {scholarship.amount.toLocaleString()}</strong>}{scholarship.application_url && <a href={scholarship.application_url} target="_blank" rel="noreferrer">Apply ↗</a>}</div></article>)}</div> : <div className="university-empty">No verified scholarship records are stored yet.</div>}</section>
      <aside className="sketch-card sketch-card-violet university-trust-note"><Icon name="info" size={28}/><div><h3>{university.data_quality === "database" ? "Stored Fence information" : "Illustrative university profile"}</h3><p>{university.data_quality === "illustrative" ? "Fees, duration and programme details are examples for comparison. Verify every decision on the official university website." : "This view reflects the records currently stored by Fence. Confirm deadlines and offers with the university."}</p></div></aside></div>
  </main>;
}
