"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import "../../styles/dashboard.css";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api/client";

type ScenarioSummary = {
  id: number;
  name: string;
  status: string;
  current_revision_number: number;
  target_role: string;
  country: string;
  currency: string;
  created_at: string;
  updated_at: string;
};

// Mock data to enrich the UI to match the design, since the summary endpoint doesn't return full details
const ENRICH_DATA = [
  { theme: "dark", studyMode: "On-campus", degree: "Bachelor's", duration: "3 years", cost: "$18,000", btn: "lime" },
  { theme: "light", studyMode: "On-campus", degree: "Bachelor's", duration: "3 years", cost: "$21,000", btn: "violet" },
  { theme: "light", studyMode: "On-campus", degree: "Bachelor's", duration: "3 years", cost: "$16,500", btn: "violet" },
  { theme: "dark", studyMode: "Online", degree: "Certificate", duration: "6 months", cost: "$3,000", btn: "lime" },
];

export default function ScenariosPage() {
  const router = useRouter();
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadScenarios() {
      try {
        setScenarios(await apiRequest<ScenarioSummary[]>("/api/simulations", { authenticated: true }));
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "Could not load saved scenarios.");
      } finally {
        setLoading(false);
      }
    }
    loadScenarios();
  }, []);

  useEffect(() => {
    if (selectedId === null) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSelectedId(null);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [selectedId]);

  const selectedScenario = scenarios.find(s => s.id === selectedId);
  const selectedEnrich = selectedScenario ? ENRICH_DATA[scenarios.indexOf(selectedScenario) % ENRICH_DATA.length] : null;
  const filteredScenarios = scenarios.filter((scenario) =>
    `${scenario.name} ${scenario.country} ${scenario.target_role}`.toLowerCase().includes(query.trim().toLowerCase())
  );

  if (loading) return <div className="dashboard-layout" style={{ paddingTop: 100 }}>Loading scenarios...</div>;

  return (
    <div className="dashboard-layout">
      
      <header className="dashboard-header" style={{ marginBottom: "24px" }}>
        <p className="dashboard-breadcrumb">Workspace <i>/</i> Saved Scenarios</p>
        <div className="dashboard-title-row">
          <h1>Your <span className="highlight-violet">saved scenarios</span></h1>
          <span className="demo-pill">DEMO DATA</span>
        </div>
        <p>Explore, compare and refine your education options.</p>
      </header>

      <div className="scenarios-page-container">
        {error && <div className="workspace-status is-error" role="alert">{error}</div>}
        <div className="scenarios-main">
          
          <div className="scenarios-toolbar">
            <div className="scenarios-search">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search scenarios by name, country or role..." />
            </div>
            <Link href="/workspace/scenario/new" className="btn-new-scenario">+ New scenario</Link>
            <span className="scenarios-count">{filteredScenarios.length} scenarios</span>
          </div>

          <div className="scenarios-grid">
            {filteredScenarios.map((scenario) => {
              const idx = scenarios.indexOf(scenario);
              const enrich = ENRICH_DATA[idx % ENRICH_DATA.length];
              const isDark = enrich.theme === "dark";
              const isActive = scenario.status === "active" || scenario.status === "complete";
              
              return (
                <div 
                  key={scenario.id} 
                  className={`sc-card ${isDark ? 'is-dark' : 'is-light'}`}
                  onClick={() => setSelectedId(scenario.id)}
                  style={{ cursor: "pointer" }}
                >
                  <div className="sc-header">
                    <div className="sc-title">
                      <small>{scenario.country}</small>
                      <strong>{scenario.name}</strong>
                    </div>
                    <div className="ws-status-pill" style={isActive ? undefined : { background: "#f4f6f8", color: "#5f6669" }}>
                      {isActive ? "Active" : "Draft"}
                    </div>
                  </div>

                  <div className="sc-details">
                    <div className="sc-info-col">
                      <div className="sc-info-label">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                        LOCATION
                      </div>
                      <span className="sc-info-val">{scenario.country}</span>
                    </div>
                    <div className="sc-info-col">
                      <div className="sc-info-label">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
                        STUDY MODE
                      </div>
                      <span className="sc-info-val">{enrich.studyMode}</span>
                    </div>
                    <div className="sc-info-col">
                      <div className="sc-info-label">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>
                        DEGREE / DURATION
                      </div>
                      <span className="sc-info-val">{enrich.degree} • {enrich.duration}</span>
                    </div>
                  </div>

                  <div className="sc-summary-strip">
                    <div>
                      <span>Target role</span>
                      <strong>{scenario.target_role || "Not selected yet"}</strong>
                    </div>
                    <div>
                      <span>Updated</span>
                      <strong>{new Intl.DateTimeFormat("en", { day: "numeric", month: "short", year: "numeric" }).format(new Date(scenario.updated_at))}</strong>
                    </div>
                  </div>

                  <div className="sc-footer">
                    <div className="sc-cost">
                      <small>ESTIMATED TOTAL COST</small>
                      <strong>{enrich.cost}</strong>
                    </div>
                    <button 
                      className={`btn-open-prediction ${enrich.btn === 'lime' ? 'btn-lime' : 'btn-violet'}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        router.push(`/workspace/scenarios/${scenario.id}`);
                      }}
                    >
                      Open full calculation →
                    </button>
                  </div>
                </div>
              );
            })}
            
            {/* If empty, show a placeholder or mock card */}
            {filteredScenarios.length === 0 && (
              <div style={{ gridColumn: "1 / -1", textAlign: "center", padding: "60px", background: "#fff", borderRadius: "16px" }}>
                <p style={{ color: "#5f6669", marginBottom: "16px" }}>{scenarios.length ? "No scenarios match your search." : "You have no saved scenarios."}</p>
                {!scenarios.length && <Link href="/workspace/scenario/new" className="btn-new-scenario">+ Create your first scenario</Link>}
              </div>
            )}
          </div>

          <div className="wi-notice" style={{ marginTop: "32px", maxWidth: "800px" }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            <div style={{ marginLeft: "4px" }}>
              <strong style={{ display: "block", color: "#524089", marginBottom: "4px" }}>Illustrative scenarios</strong>
              <p>These scenarios are examples based on publicly available information and estimated costs. Actual details may vary and must be verified through official university sources.</p>
            </div>
          </div>
        </div>

        {/* Side Panel */}
        {selectedScenario && selectedEnrich && (
          <aside className="scenarios-side-panel">
            <button className="sp-close" type="button" aria-label="Close scenario details" onClick={() => setSelectedId(null)}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>

            <div className="sp-header">
              <small>WSiiZ • {selectedScenario.country}</small>
              <h2>{selectedScenario.name} • {selectedEnrich.degree}</h2>
              <p>Explore your saved study scenario and next steps.</p>
            </div>

            <div className="sp-facts">
              <div className="sp-fact">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                <div className="sp-fact-text">
                  <span>Duration</span>
                  <span>{selectedEnrich.duration}</span>
                </div>
              </div>
              <div className="sp-fact">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
                <div className="sp-fact-text">
                  <span>Study mode</span>
                  <span>{selectedEnrich.studyMode}</span>
                </div>
              </div>
              <div className="sp-fact">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                <div className="sp-fact-text">
                  <span>Total tuition</span>
                  <span>{selectedEnrich.cost} (demo)</span>
                </div>
              </div>
              <div className="sp-fact">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                <div className="sp-fact-text">
                  <span>Target role</span>
                  <span style={{ fontWeight: 400, color: "#5f6669" }}>Not set – added after Roadmap</span>
                </div>
              </div>
            </div>

            <h3 className="sp-actions-title">Explore and plan</h3>
            <div className="sp-actions-list">
              <Link className="sp-action-item" href={`/workspace/scenarios/${selectedScenario.id}#investment`}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
                <div className="sp-action-content">
                  <strong>Investment breakdown</strong>
                  <p>Review tuition, opportunity cost and the total investment.</p>
                </div>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
              </Link>
              
              <Link className="sp-action-item" href={`/workspace/scenarios/${selectedScenario.id}#trajectory`}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
                <div className="sp-action-content">
                  <strong>Salary trajectory</strong>
                  <p>Compare projected and baseline salary by year.</p>
                </div>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
              </Link>
              
              <Link className="sp-action-item" href={`/workspace/scenarios/${selectedScenario.id}#evidence`}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                <div className="sp-action-content">
                  <strong>Evidence &amp; assumptions</strong>
                  <p>Inspect sources, methodology and values requiring review.</p>
                </div>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
              </Link>
            </div>

            <Link href={`/workspace/scenarios/${selectedScenario.id}`} className="btn-sp-full" style={{ textDecoration: 'none' }}>
              Open full calculation
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>
            </Link>
            <span className="sp-footer-note">Includes investment, salary, payback, evidence and calculation assumptions.</span>
          </aside>
        )}

      </div>
    </div>
  );
}
