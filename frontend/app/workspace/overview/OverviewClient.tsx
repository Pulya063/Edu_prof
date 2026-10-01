"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import "../../styles/dashboard.css";

// ── Types ─────────────────────────────────────────────────────────────
type Revision = {
  revision_number: number;
  assumptions: any;
  created_at: string;
};

type OverviewResponse = {
  status: "empty" | "scenario_only" | "projected";
  scenario: null | {
    id: number;
    name: string;
    current_revision_number: number;
    target_role: string;
    country: string;
    currency: string;
    revisions: Revision[];
  };
  projection: any | null;
  explainability: any | null;
};

type ScenarioSummary = {
  id: number;
  name: string;
  status: string;
  country: string;
};

export default function OverviewClient() {
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [savedScenarios, setSavedScenarios] = useState<ScenarioSummary[]>([]);
  const [roadmap, setRoadmap] = useState<any>(null);
  const [state, setState] = useState<"loading" | "ready" | "unauthorized" | "error">("loading");

  const loadOverview = useCallback(async (signal?: AbortSignal) => {
    setState("loading");
    try {
      const [overviewRes, scenariosRes, roadmapRes] = await Promise.all([
        fetch("/api/simulations/overview", { headers: { Accept: "application/json" }, signal }),
        fetch("/api/simulations", { headers: { Accept: "application/json" }, signal }),
        fetch("/api/roadmap", { headers: { Accept: "application/json" }, signal })
      ]);
      
      if (overviewRes.status === 401) {
        setState("unauthorized");
        return;
      }
      if (!overviewRes.ok) throw new Error(`Overview request failed: ${overviewRes.status}`);
      
      const overviewData = await overviewRes.json();
      const scenariosData = scenariosRes.ok ? await scenariosRes.json() : [];
      let roadmapData = null;
      if (roadmapRes.ok) {
        const parsed = await roadmapRes.json();
        if (parsed.success) roadmapData = parsed.data;
      }

      setData(overviewData);
      setSavedScenarios(scenariosData);
      setRoadmap(roadmapData);
      setState("ready");
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      setState("error");
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void loadOverview(controller.signal);
    return () => controller.abort();
  }, [loadOverview]);

  if (state === "loading") {
    return <div className="dashboard-layout" style={{ paddingTop: 100 }}>Loading dashboard...</div>;
  }
  if (state === "unauthorized") {
    return <div className="dashboard-layout">Please sign in to view your dashboard.</div>;
  }

  // Derive real data values
  const hasActive = data && data.status !== "empty" && data.scenario;
  const activeScenarioName = hasActive ? data.scenario!.name : "Computer Science";
  const activeAssumptions = hasActive && data.scenario!.revisions ? data.scenario!.revisions.at(-1)?.assumptions : null;
  const university = activeAssumptions?.university || "Your University";
  const location = activeAssumptions?.country || data?.scenario?.country || "Location";
  const targetRole = activeAssumptions?.career_target || data?.scenario?.target_role || "Role not set";
  
  // Projection data
  const hasProjection = data?.status === "projected" && data.projection;
  const projection = data?.projection;
  const fmtCurrency = (val: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: projection?.currency || 'USD', maximumFractionDigits: 0 }).format(val);
  };

  return (
    <div className="dashboard-layout">
      
      {/* ── Header ── */}
      <header className="dashboard-header">
        <p className="dashboard-breadcrumb">Workspace <i>/</i> Overview</p>
        <div className="dashboard-title-row">
          <h1>Your <span className="highlight-violet">next move</span>, Andrii.</h1>
          {!hasActive && <span className="demo-pill">DEMO DATA</span>}
        </div>
        <p>Turn your education choice into a clear career plan.</p>
        <Link href="/workspace/scenario/new" className="btn-new-scenario">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14M5 12h14"/></svg>
          New scenario
        </Link>
      </header>

      {/* ── Grid ── */}
      <div className="dashboard-grid">
        
        {/* Widget 1: Active Scenario & Financials */}
        <div className="widget widget-scenario">
          <div className="ws-top-row">
            <span className="ws-label">YOUR ACTIVE SCENARIO</span>
            <div className="ws-status-pill">{hasActive ? "Active" : "Demo"}</div>
          </div>
          <h2>{activeScenarioName}</h2>
          <p className="ws-subtitle">{university} • {location} • On campus</p>
          <div className="ws-target">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>
            Target role: {targetRole}
          </div>
          
          {hasProjection ? (
            <div style={{ marginTop: "32px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", borderTop: "1px solid rgba(255,255,255,0.1)", paddingTop: "24px" }}>
              <div>
                <span style={{ display: "block", fontSize: "11px", color: "#aeb5bb", fontWeight: 700, letterSpacing: "0.05em", marginBottom: "4px" }}>TOTAL INVESTMENT</span>
                <strong style={{ fontSize: "24px", color: "#B7FF2A", fontWeight: 800 }}>{fmtCurrency(projection.total_investment)}</strong>
              </div>
              <div>
                <span style={{ display: "block", fontSize: "11px", color: "#aeb5bb", fontWeight: 700, letterSpacing: "0.05em", marginBottom: "4px" }}>STARTING SALARY</span>
                <strong style={{ fontSize: "24px", color: "#fff", fontWeight: 800 }}>{fmtCurrency(projection.estimated_start_salary)}</strong>
              </div>
              <div>
                <span style={{ display: "block", fontSize: "11px", color: "#aeb5bb", fontWeight: 700, letterSpacing: "0.05em", marginBottom: "4px" }}>ROI</span>
                <strong style={{ fontSize: "24px", color: "#fff", fontWeight: 800 }}>{projection.roi_percent ? `${projection.roi_percent}%` : 'N/A'}</strong>
              </div>
              <div>
                <span style={{ display: "block", fontSize: "11px", color: "#aeb5bb", fontWeight: 700, letterSpacing: "0.05em", marginBottom: "4px" }}>PAYBACK PERIOD</span>
                <strong style={{ fontSize: "24px", color: "#fff", fontWeight: 800 }}>{projection.payback_months ? `${Math.round(projection.payback_months/12 * 10)/10} yrs` : 'N/A'}</strong>
              </div>
            </div>
          ) : (
            <div className="ws-bottom-row">
              <div className="ws-info-block">
                <div className="ws-info-block-top">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
                  FIELD
                </div>
                <strong>{activeScenarioName}</strong>
              </div>
              <div className="ws-info-block">
                <div className="ws-info-block-top">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                  LOCATION
                </div>
                <strong>{location}</strong>
              </div>
            </div>
          )}
        </div>

        {/* Widget 2: Career insights */}
        <div className="widget widget-insights">
          <div className="wi-header">
            <h3>Career insights</h3>
            <span>Based on your target — {targetRole}</span>
          </div>
          <div className="wi-controls">
            <div className="wi-tabs">
              <button type="button" className="wi-tab is-active">All</button>
              <button type="button" className="wi-tab">YouTube</button>
              <button type="button" className="wi-tab">Public web</button>
            </div>
            <div className="wi-search">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input type="text" placeholder="Find resources" />
            </div>
          </div>
          <div className="wi-list">
            <div className="wi-item">
              <div className="wi-item-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg></div>
              <div className="wi-item-content">
                <strong>{targetRole.split(' ')[0]} project walkthrough</strong>
                <p>Step-by-step project to build a real-world application.</p>
              </div>
              <div className="wi-item-meta">
                <span className="wi-item-tag tag-youtube">YouTube</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>
              </div>
            </div>
            <div className="wi-item">
              <div className="wi-item-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg></div>
              <div className="wi-item-content">
                <strong>{activeScenarioName} hiring trends</strong>
                <p>Key skills in 2024 and what employers look for.</p>
              </div>
              <div className="wi-item-meta">
                <span className="wi-item-tag tag-web">Public web</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>
              </div>
            </div>
          </div>
          <div className="wi-notice">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            <p><strong>Roadmap created:</strong> resources match your career plan.<br/>No roadmap: labour-market insights match your faculty.</p>
          </div>
        </div>

        {/* Widget 3: Saved Scenarios */}
        <div className="widget widget-saved">
          <h3 className="wsaved-title">Saved scenarios</h3>
          <table className="wsaved-table">
            <thead>
              <tr>
                <th>SCENARIO</th>
                <th>LOCATION</th>
                <th>STATUS</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {savedScenarios.length > 0 ? savedScenarios.slice(0, 3).map(scenario => (
                <tr key={scenario.id}>
                  <td className="td-scenario">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
                    {scenario.name}
                  </td>
                  <td>{scenario.country}</td>
                  <td className="td-status">
                    <span className={`status-badge ${scenario.status === 'active' || scenario.status === 'complete' ? 'status-active' : 'status-draft'}`}>
                      {scenario.status}
                    </span>
                  </td>
                  <td className="td-arrow">
                    <Link href="/workspace/scenarios"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg></Link>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={4} style={{ textAlign: "center", padding: "24px", color: "#858e94" }}>No scenarios saved yet.</td>
                </tr>
              )}
            </tbody>
          </table>
          <Link href="/workspace/scenarios" className="wsaved-link">
            View all scenarios
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>
          </Link>
        </div>

        {/* Widget 4: Career Roadmap */}
        <div className="widget widget-roadmap">
          <div className="wrm-header">
            <h3 className="wrm-title">Your career <span className="wrm-highlight">roadmap</span></h3>
            <div className="wrm-progress">
              <span>{roadmap ? roadmap.roadmap_data.tasks.filter((t: any) => t.status === "completed").length : 0} of {roadmap ? roadmap.roadmap_data.tasks.length : 12} tasks completed</span>
              <div className="wrm-bar">
                <div className="wrm-bar-fill" style={{ width: roadmap ? `${(roadmap.roadmap_data.tasks.filter((t: any) => t.status === "completed").length / roadmap.roadmap_data.tasks.length) * 100}%` : '0%' }}></div>
              </div>
            </div>
          </div>
          <div className="wrm-list">
            {roadmap ? (
              roadmap.roadmap_data.tasks.slice(0, 3).map((task: any, idx: number) => (
                <div className="wrm-item" key={idx}>
                  <div className="wrm-item-left">
                    <svg className="icon-circle" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/></svg>
                    {task.title}
                  </div>
                  <div className={`wrm-status txt-${task.status === "completed" ? "completed" : task.status === "in_progress" ? "progress" : "upcoming"}`}>
                    {task.status === "completed" ? "Completed" : task.status === "in_progress" ? "In progress" : "Upcoming"}
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
                  </div>
                </div>
              ))
            ) : (
              <>
                <div className="wrm-item">
                  <div className="wrm-item-left">
                    <svg className="icon-circle" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/></svg>
                    {activeScenarioName} fundamentals
                  </div>
                  <div className="wrm-status txt-progress">
                    In progress
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
                  </div>
                </div>
                <div className="wrm-item">
                  <div className="wrm-item-left">
                    <svg className="icon-circle" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/></svg>
                    Build your first project
                  </div>
                  <div className="wrm-status txt-upcoming">
                    Upcoming
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
                  </div>
                </div>
              </>
            )}
          </div>
          {roadmap ? (
            <Link href="/workspace/roadmap" className="wrm-link">
              Continue roadmap
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>
            </Link>
          ) : (
            <span className="wrm-link" style={{ opacity: 0.5, cursor: "not-allowed" }}>
              Roadmap builder planned
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>
            </span>
          )}
        </div>

        {/* Widget 5: Banner */}
        <div className="widget widget-banner">
          <div className="wbn-left">
            <h3>Start small.<br/>Move with clarity.</h3>
          </div>
          <div className="wbn-center">
            Compare universities, costs and career outcomes — and find the path that fits your goals.
          </div>
          <div className="wbn-right">
            <span className="wbn-btn" style={{ opacity: 0.5, cursor: "not-allowed" }}>
              Comparison tool planned
            </span>
          </div>
        </div>

      </div>
    </div>
  );
}
