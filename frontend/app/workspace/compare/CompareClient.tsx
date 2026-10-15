"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Icon, Topography, WorkspacePageHeader } from "../WorkspaceUI";
import { WorkspaceUniversity, workspaceFetch } from "@/lib/api/workspace";

export default function CompareClient() {
  const [country, setCountry] = useState("Poland");
  const [faculty, setFaculty] = useState("Computer Science");
  const [query, setQuery] = useState("");
  const [universities, setUniversities] = useState<WorkspaceUniversity[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setLoading(true); setError("");
      const params = new URLSearchParams({ country, faculty, q: query });
      workspaceFetch<WorkspaceUniversity[]>(`/api/workspace/universities?${params}`, { signal: controller.signal }).then((items) => { setUniversities(items); setSelectedId((current) => items.some((item) => item.id === current) ? current : ""); }).catch((reason) => { if (reason.name !== "AbortError") setError(reason.message); }).finally(() => setLoading(false));
    }, 250);
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, [country, faculty, query]);

  useEffect(() => {
    if (!selectedId) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSelectedId("");
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [selectedId]);
  const selected = universities.find((item) => item.id === selectedId);

  return (
    <main className="sketch-page">
      <WorkspacePageHeader section="Compare Universities" title="Compare your education options" highlight="education options" description="Explore universities, compare key details and find the best fit for your goals.">
        <div className="sketch-card compare-toolbar">
          <label className="sketch-field"><Icon name="globe" /><div><small>Country</small><select value={country} onChange={(event) => setCountry(event.target.value)}><option>Poland</option></select></div></label>
          <label className="sketch-field"><Icon name="graduation" /><div><small>Faculty</small><select value={faculty} onChange={(event) => setFaculty(event.target.value)}><option>Computer Science</option><option>Data Analytics</option></select></div></label>
          <label className="sketch-field"><Icon name="search" /><input value={query} onChange={(event) => setQuery(event.target.value)} aria-label="Search university" placeholder="Search university..." /></label>
          <button type="button" disabled className="sketch-btn sketch-btn-violet" title="External directory integration is not configured">External directory unavailable</button>
        </div>
      </WorkspacePageHeader>
      {error && <div className="workspace-status is-error">{error}</div>}
      <p className="compare-found">{loading ? "Loading universities…" : `${universities.length} universities found`}</p>
      <div className="compare-layout">
        <section className="university-grid" aria-label="University results">
          {universities.map((university, index) => (
            <button type="button" className={`sketch-card university-card ${index === 0 ? "is-featured" : ""} ${selectedId === university.id ? "is-selected" : ""}`} key={university.id} onClick={() => setSelectedId(university.id)}>
              {index === 0 && <Topography />}
              <div className="university-brand"><span className="university-mark">{university.name.split(/\s+/).map((part) => part[0]).join("").slice(0, 3)}</span><div><h2>{university.name}</h2><div className="location"><Icon name="pin" size={15} /> {university.city || university.country}, {university.country}</div></div></div>
              <div className="university-stats"><div><strong>{university.annual_tuition == null ? "—" : new Intl.NumberFormat("en", { style: "currency", currency: university.currency, maximumFractionDigits: 0 }).format(university.annual_tuition)}</strong><span>Annual tuition</span></div><div><strong>{university.duration_years ? `${university.duration_years} years` : "—"}</strong><span>Duration</span></div><div><strong>{university.study_mode}</strong><span>Study mode</span></div></div>
            </button>
          ))}
          {!loading && !universities.length && <div className="workspace-status">No universities match these filters.</div>}
        </section>
        {selected && (
          <>
            <button type="button" className="university-detail-backdrop" aria-label="Close university details" onClick={() => setSelectedId("")} />
            <aside className="sketch-card university-detail" role="dialog" aria-label={`${selected.name} details`}>
              <button type="button" className="university-detail-close" aria-label="Close university details" onClick={() => setSelectedId("")}>×</button>
              <div className="university-detail-hero"><Topography/><div className="university-brand"><span className="university-mark">{selected.name[0]}</span><div><h2>{selected.name}</h2><p>{selected.program_name}</p></div></div></div>
              <div className="university-detail-tabs"><strong>Prediction</strong><Link href={`/workspace/universities/${encodeURIComponent(selected.id)}`}>About</Link></div>
              <h3>Education investment <small>({selected.data_quality})</small></h3>
              <div className="detail-investment"><div><strong>{selected.annual_tuition == null ? "—" : `${selected.currency} ${selected.annual_tuition.toLocaleString()}`}</strong><span>Annual tuition</span></div><div><strong>{selected.duration_years ? `${selected.duration_years} years` : "—"}</strong><span>Duration</span></div><div><strong>{selected.annual_tuition && selected.duration_years ? `${selected.currency} ${(selected.annual_tuition * selected.duration_years).toLocaleString()}` : "—"}</strong><span>Total</span></div></div>
              <h3>Programme</h3>
              <p>{selected.description}</p>
              {selected.website ? <a className="sketch-btn" href={selected.website} target="_blank" rel="noreferrer">Open official website <Icon name="arrow" size={17}/></a> : <button className="sketch-btn" disabled>Website unavailable</button>}
              <Link href={`/workspace/universities/${encodeURIComponent(selected.id)}`} className="sketch-btn sketch-btn-primary">Open full university details <Icon name="arrow" size={17}/></Link>
              <div className="sketch-card sketch-card-violet settings-note"><Icon name="info"/><div><strong>{selected.data_quality === "database" ? "Stored university data" : "Illustrative comparison"}</strong>{selected.data_quality === "illustrative" ? "Verify fees and programme details on the official university website." : "This information comes from the Fence database."}</div></div>
            </aside>
          </>
        )}
      </div>
    </main>
  );
}
