"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api/client";
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

type WorkspaceResource = {
  id: string;
  title: string;
  description: string;
  source: "Public web" | "YouTube";
  url: string;
  skills: string[];
};

type ResourceSource = "" | WorkspaceResource["source"];

export default function OverviewClient() {
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [savedScenarios, setSavedScenarios] = useState<ScenarioSummary[]>([]);
  const [roadmap, setRoadmap] = useState<any>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [resources, setResources] = useState<WorkspaceResource[]>([]);
  const [resourceQuery, setResourceQuery] = useState("");
  const [resourceSource, setResourceSource] = useState<ResourceSource>("");
  const [resourceState, setResourceState] = useState<"loading" | "ready" | "error">("loading");

  const loadOverview = useCallback(async (signal?: AbortSignal) => {
    setState("loading");
    try {
      const [overviewData, scenariosData, workspaceData] = await Promise.all([
        apiRequest<OverviewResponse>("/api/simulations/overview", { signal, authenticated: true }),
        apiRequest<ScenarioSummary[]>("/api/simulations", { signal, authenticated: true }),
        apiRequest<{ roadmap: unknown }>("/api/workspace", { signal, authenticated: true }),
      ]);

      setData(overviewData);
      setSavedScenarios(scenariosData);
      setRoadmap(workspaceData.roadmap);
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

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setResourceState("loading");
      try {
        const params = new URLSearchParams();
        if (resourceQuery.trim()) params.set("q", resourceQuery.trim());
        if (resourceSource) params.set("source", resourceSource);
        const matchedResources = await apiRequest<WorkspaceResource[]>(`/api/workspace/resources?${params.toString()}`, {
          signal: controller.signal,
          authenticated: true,
        });
        setResources(matchedResources);
        setResourceState("ready");
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setResourceState("error");
      }
    }, 250);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [resourceQuery, resourceSource]);

  if (state === "loading") {
    return <div className="dashboard-layout" style={{ paddingTop: 100 }}>Loading dashboard...</div>;
  }
  // Derive real data values
  const hasActive = data && data.status !== "empty" && data.scenario;
  const activeScenarioName = hasActive ? data.scenario!.name : "Computer Science";
  const activeAssumptions = hasActive && data.scenario!.revisions ? data.scenario!.revisions.at(-1)?.assumptions : null;
  const university = activeAssumptions?.university || "Your University";
  const location = activeAssumptions?.country || data?.scenario?.country || "Location";
  const targetRole = activeAssumptions?.career_target || data?.scenario?.target_role || "Role not set";
  const roadmapTasks = roadmap?.plan?.phases?.flatMap((phase: any) => phase.tasks || []) || [];
  const completedRoadmapTasks = roadmapTasks.filter((task: any) => task.completed);
  
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
              {(["", "YouTube", "Public web"] as ResourceSource[]).map((source) => (
                <button key={source || "all"} type="button" className={`wi-tab ${resourceSource === source ? "is-active" : ""}`} onClick={() => setResourceSource(source)}>
                  {source || "All"}
                </button>
              ))}
            </div>
            <label className="wi-search">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input type="search" value={resourceQuery} onChange={(event) => setResourceQuery(event.target.value)} placeholder="Find resources" aria-label="Search career resources" />
            </label>
          </div>
          <div className="wi-list">
            {resourceState === "loading" && <div className="wi-resource-state">Loading matched resources…</div>}
            {resourceState === "error" && <div className="wi-resource-state is-error">Resources are temporarily unavailable.</div>}
            {resourceState === "ready" && resources.length === 0 && <div className="wi-resource-state">No resources match these filters.</div>}
            {resourceState === "ready" && resources.slice(0, 3).map((resource) => (
              <a className="wi-item" href={resource.url} target="_blank" rel="noreferrer" key={resource.id}>
                <div className="wi-item-icon">{resource.source === "YouTube" ? <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg> : <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>}</div>
                <div className="wi-item-content"><strong>{resource.title}</strong><p>{resource.description}</p></div>
                <div className="wi-item-meta"><span className={`wi-item-tag ${resource.source === "YouTube" ? "tag-youtube" : "tag-web"}`}>{resource.source}</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg></div>
              </a>
            ))}
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
                    <Link href={`/workspace/scenarios/${scenario.id}`} aria-label={`Open ${scenario.name} calculation`}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg></Link>
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
              <span>{completedRoadmapTasks.length} of {roadmapTasks.length} tasks completed</span>
              <div className="wrm-bar">
                <div className="wrm-bar-fill" style={{ width: roadmapTasks.length ? `${(completedRoadmapTasks.length / roadmapTasks.length) * 100}%` : '0%' }}></div>
              </div>
            </div>
          </div>
          <div className="wrm-list">
            {roadmapTasks.length ? (
              roadmapTasks.slice(0, 3).map((task: any, idx: number) => (
                <div className="wrm-item" key={idx}>
                  <div className="wrm-item-left">
                    <svg className="icon-circle" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/></svg>
                    {task.title}
                  </div>
                  <div className={`wrm-status txt-${task.completed ? "completed" : "progress"}`}>
                    {task.completed ? "Completed" : "In progress"}
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
            <Link href="/workspace/roadmap/plan" className="wrm-link">
              Continue roadmap
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>
            </Link>
          ) : (
            <Link href="/workspace/roadmap/simulation" className="wrm-link">Create roadmap<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg></Link>
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
            <Link href="/workspace/compare" className="wbn-btn">Compare your options</Link>
          </div>
        </div>

      </div>
    </div>
  );
}
