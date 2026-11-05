"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Icon, Topography, WorkspacePageHeader } from "../WorkspaceUI";
import { WorkspaceUniversity, WorkspaceUniversityDetails, workspaceFetch } from "@/lib/api/workspace";
import UniversityDetails from "../universities/UniversityDetails";
import "../../styles/compare-split.css";

const SELECTED_PARAM = "university";

function readSelectedFromUrl(): string {
  return new URLSearchParams(window.location.search).get(SELECTED_PARAM) || "";
}

function urlWithSelected(id: string): string {
  const url = new URL(window.location.href);
  if (id) url.searchParams.set(SELECTED_PARAM, id); else url.searchParams.delete(SELECTED_PARAM);
  return `${url.pathname}${url.search}${url.hash}`;
}

export default function CompareClient() {
  const [country, setCountry] = useState("Poland");
  const [faculty, setFaculty] = useState("Computer Science");
  const [query, setQuery] = useState("");
  const [universities, setUniversities] = useState<WorkspaceUniversity[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [details, setDetails] = useState<WorkspaceUniversityDetails | null>(null);
  const [detailsError, setDetailsError] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  // True while the open panel owns a history entry, so closing can pop it instead of stacking entries.
  const pushedEntry = useRef(false);
  const panelHeading = useRef<HTMLHeadingElement>(null);
  const returnFocusId = useRef("");

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setLoading(true); setError("");
      const params = new URLSearchParams({ country, faculty, q: query });
      workspaceFetch<WorkspaceUniversity[]>(`/api/workspace/universities?${params}`, { signal: controller.signal }).then(setUniversities).catch((reason) => { if (reason.name !== "AbortError") setError(reason.message); }).finally(() => setLoading(false));
    }, 250);
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, [country, faculty, query]);

  // A shared or reloaded link (?university=…) opens the panel; browser Back closes it.
  useEffect(() => {
    setSelectedId(readSelectedFromUrl());
    const syncFromUrl = () => { pushedEntry.current = false; setSelectedId(readSelectedFromUrl()); };
    window.addEventListener("popstate", syncFromUrl);
    return () => window.removeEventListener("popstate", syncFromUrl);
  }, []);

  useEffect(() => {
    if (!selectedId) { setDetails(null); return; }
    const controller = new AbortController();
    setDetails(null); setDetailsError("");
    workspaceFetch<WorkspaceUniversityDetails>(`/api/workspace/universities/${encodeURIComponent(selectedId)}`, { signal: controller.signal })
      .then(setDetails)
      .catch((reason) => { if (reason.name !== "AbortError") setDetailsError(reason.message); });
    return () => controller.abort();
  }, [selectedId]);

  const open = useCallback((id: string) => {
    returnFocusId.current = id;
    if (id === readSelectedFromUrl()) return;
    if (readSelectedFromUrl()) window.history.replaceState(window.history.state, "", urlWithSelected(id));
    else { window.history.pushState(window.history.state, "", urlWithSelected(id)); pushedEntry.current = true; }
    setSelectedId(id);
  }, []);

  const close = useCallback(() => {
    if (pushedEntry.current) { pushedEntry.current = false; window.history.back(); }
    else window.history.replaceState(window.history.state, "", urlWithSelected(""));
    setSelectedId("");
  }, []);

  // Esc closes; the sidebar folds to icons while the panel is open; mobile locks the page behind the full-screen panel.
  useEffect(() => {
    if (!selectedId) return;
    const root = document.documentElement;
    root.dataset.wsRail = "collapsed";
    root.dataset.wsDetailOpen = "true";
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") close(); };
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      delete root.dataset.wsRail;
      delete root.dataset.wsDetailOpen;
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [selectedId, close]);

  useEffect(() => {
    if (selectedId) { panelHeading.current?.focus({ preventScroll: true }); return; }
    if (returnFocusId.current) {
      document.querySelector<HTMLElement>(`[data-university-id="${CSS.escape(returnFocusId.current)}"]`)?.focus({ preventScroll: true });
    }
  }, [selectedId]);

  const selected = universities.find((item) => item.id === selectedId);
  const title = details?.name || selected?.name || "University";

  return (
    <main className="sketch-page compare-page">
      <WorkspacePageHeader section="Compare Universities" title="Compare your education options" highlight="education options" description="Explore universities, compare key details and find the best fit for your goals." >
        <div className="sketch-card compare-toolbar">
          <label className="sketch-field"><Icon name="globe" /><div><small>Country</small><select value={country} onChange={(event) => setCountry(event.target.value)}><option>Poland</option><option>Ukraine</option></select></div></label>
          <label className="sketch-field"><Icon name="graduation" /><div><small>Faculty</small><select value={faculty} onChange={(event) => setFaculty(event.target.value)}><option>Computer Science</option><option>Data Analytics</option></select></div></label>
          <label className="sketch-field"><Icon name="search" /><input value={query} onChange={(event) => setQuery(event.target.value)} aria-label="Search university" placeholder="Search university..." /></label>
        </div>
      </WorkspacePageHeader>
      {error && <div className="workspace-status is-error">{error}</div>}
      <p className="compare-found">{loading ? "Loading universities…" : `${universities.length} universities found`}</p>
      <div className={`compare-layout ${selectedId ? "has-detail" : ""}`}>
        <section className="university-grid" aria-label="University results">
          {universities.map((university, index) => (
            <button
              type="button"
              className={`sketch-card university-card ${index === 0 && !selectedId ? "is-featured" : ""} ${selectedId === university.id ? "is-selected" : ""}`}
              key={university.id}
              data-university-id={university.id}
              aria-pressed={selectedId === university.id}
              aria-controls={selectedId ? "university-panel" : undefined}
              onClick={() => open(university.id)}
            >
              {index === 0 && !selectedId && <Topography />}
              <div className="university-brand"><span className="university-mark">{university.name.split(/\s+/).map((part) => part[0]).join("").slice(0, 3)}</span><div><h2>{university.name}</h2><div className="location"><Icon name="pin" size={15} /> {university.city || university.country}, {university.country}</div></div></div>
              <div className="university-stats"><div><strong>{university.annual_tuition == null || !university.currency ? "—" : new Intl.NumberFormat("en", { style: "currency", currency: university.currency, maximumFractionDigits: 0 }).format(university.annual_tuition)}</strong><span>Annual tuition</span></div><div><strong>{university.duration_years ? `${university.duration_years} years` : "—"}</strong><span>Duration</span></div><div><strong>{university.website ? university.website.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, "") : "—"}</strong><span>Website</span></div></div>
            </button>
          ))}
          {!loading && !universities.length && <div className="workspace-status">No universities match these filters.</div>}
        </section>
        {selectedId && (
          <aside id="university-panel" className="university-panel" aria-labelledby="university-panel-title">
            <header className="university-panel-bar">
              <button type="button" className="university-panel-back" onClick={close}><span aria-hidden="true">←</span> Universities</button>
              <h2 id="university-panel-title" ref={panelHeading} tabIndex={-1}>{title}</h2>
              <Link href={`/workspace/universities/${encodeURIComponent(selectedId)}`} className="university-panel-full">Full page</Link>
              <button type="button" className="university-panel-close" aria-label="Close university details" onClick={close}>×</button>
            </header>
            <div className="university-panel-body">
              {detailsError ? <div className="workspace-status is-error">{detailsError}</div>
                : details ? <UniversityDetails university={details} compact />
                : <div className="workspace-status" role="status">Loading university details…</div>}
            </div>
          </aside>
        )}
      </div>
    </main>
  );
}
