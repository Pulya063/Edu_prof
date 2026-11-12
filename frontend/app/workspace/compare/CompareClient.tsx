"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Icon, Topography, WorkspacePageHeader } from "../WorkspaceUI";
import { WorkspaceUniversity, WorkspaceUniversityDetails, workspaceFetch } from "@/lib/api/workspace";
import UniversityDetails from "../universities/UniversityDetails";
import Dropdown, { type DropdownOption } from "./Dropdown";
import { foldRail } from "@/lib/railState";
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

const SORTS: DropdownOption[] = [
  { value: "relevance", label: "Most relevant" },
  { value: "fee_low", label: "Lowest tuition" },
  { value: "fee_high", label: "Highest tuition" },
  { value: "programmes", label: "Most programmes" },
  { value: "name", label: "Name A–Z" },
];
const COUNTRIES: DropdownOption[] = [{ value: "Poland", label: "Poland" }, { value: "Ukraine", label: "Ukraine" }];
const QUICK_PROGRAMMES = ["Informatyka", "Medycyna", "Prawo", "Ekonomia", "Psychologia", "Zarządzanie"];

type Search = { q: string; programme: string; city: string };
const EMPTY_SEARCH: Search = { q: "", programme: "", city: "" };

function money(value: number, currency: string) {
  return new Intl.NumberFormat("en", { style: "currency", currency, maximumFractionDigits: 0 }).format(value);
}

export default function CompareClient() {
  const [country, setCountry] = useState("Poland");
  // What is typed in the bar; the list only changes when Search is pressed (or Enter).
  const [draft, setDraft] = useState<Search>(EMPTY_SEARCH);
  const [search, setSearch] = useState<Search>(EMPTY_SEARCH);
  const [hasFees, setHasFees] = useState(false);
  const [sort, setSort] = useState("relevance");
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
    setLoading(true); setError("");
    const params = new URLSearchParams({ country, q: search.q, programme: search.programme, city: search.city, sort, limit: "60", ...(hasFees ? { has_fees: "1" } : {}) });
    workspaceFetch<WorkspaceUniversity[]>(`/api/workspace/universities?${params}`, { signal: controller.signal })
      .then(setUniversities)
      .catch((reason) => { if (reason.name !== "AbortError") setError(reason.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [country, search, hasFees, sort]);

  function runSearch(next: Search = draft) {
    setDraft(next);
    setSearch({ q: next.q.trim(), programme: next.programme.trim(), city: next.city.trim() });
  }

  const activeFilters = [
    search.q && { key: "q", label: `Name: ${search.q}` },
    search.programme && { key: "programme", label: `Programme: ${search.programme}` },
    search.city && { key: "city", label: `City: ${search.city}` },
    hasFees && { key: "fees", label: "Published fees" },
  ].filter(Boolean) as { key: string; label: string }[];

  function clearFilter(key: string) {
    if (key === "fees") { setHasFees(false); return; }
    runSearch({ ...draft, [key]: "" });
  }

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
    const unfoldRail = foldRail();
    root.dataset.wsDetailOpen = "true";
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") close(); };
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      unfoldRail();
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
        <form className="compare-search" role="search" onSubmit={(event) => { event.preventDefault(); runSearch(); }}>
          <label className="compare-search-field is-main"><Icon name="search" /><input value={draft.q} onChange={(event) => setDraft({ ...draft, q: event.target.value })}
            autoComplete="off" aria-label="University name" placeholder="University name" /></label>
          <label className="compare-search-field"><Icon name="graduation" /><input value={draft.programme} onChange={(event) => setDraft({ ...draft, programme: event.target.value })}
            autoComplete="off" aria-label="Programme" placeholder="Programme, e.g. Informatyka" /></label>
          <label className="compare-search-field"><Icon name="pin" /><input value={draft.city} onChange={(event) => setDraft({ ...draft, city: event.target.value })}
            autoComplete="off" aria-label="City" placeholder="City" /></label>
          <button type="submit" className="compare-search-button">Search</button>
        </form>
        <div className="compare-filters">
          <Dropdown label="Country" value={country} options={COUNTRIES} onChange={setCountry} icon={<Icon name="globe" size={17} />} />
          <button type="button" className={`compare-chip ${hasFees ? "is-on" : ""}`} aria-pressed={hasFees} onClick={() => setHasFees(!hasFees)}>Published fees</button>
          {QUICK_PROGRAMMES.map((name) => (
            <button key={name} type="button" className={`compare-chip ${search.programme === name ? "is-on" : ""}`} aria-pressed={search.programme === name}
              onClick={() => runSearch({ ...draft, programme: search.programme === name ? "" : name })}>{name}</button>
          ))}
          <div className="compare-sort"><Dropdown label="Sort by" value={sort} options={SORTS} onChange={setSort} /></div>
        </div>
      </WorkspacePageHeader>
      {error && <div className="workspace-status is-error">{error}</div>}
      <div className="compare-found">
        <p>{loading ? "Loading universities…" : `${universities.length} universities found`}</p>
        {activeFilters.length ? <ul className="compare-active">{activeFilters.map((filter) => (
          <li key={filter.key}><button type="button" onClick={() => clearFilter(filter.key)} aria-label={`Remove filter ${filter.label}`}>{filter.label} <span aria-hidden="true">×</span></button></li>
        ))}<li><button type="button" className="is-reset" onClick={() => { setHasFees(false); runSearch(EMPTY_SEARCH); }}>Clear all</button></li></ul> : null}
      </div>
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
              <div className="university-stats">
                <div><strong>{university.fee_min != null && university.fee_currency
                  ? `${university.fee_max != null && university.fee_max !== university.fee_min ? "from " : ""}${money(university.fee_min, university.fee_currency)}`
                  : university.annual_tuition != null && university.currency ? money(university.annual_tuition, university.currency) : "—"}</strong><span>Tuition a year</span></div>
                <div><strong>{university.programme_count ?? "—"}</strong><span>Programmes</span></div>
                <div><strong>{university.website ? university.website.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, "") : "—"}</strong><span>Website</span></div>
              </div>
              {university.verified_facts ? <span className="university-verified">Verified data</span> : null}
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
