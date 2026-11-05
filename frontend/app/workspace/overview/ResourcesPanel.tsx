"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api/client";
import type { WorkspaceResourceResponse } from "@/lib/api/generated";

type ResourceSource = "" | WorkspaceResourceResponse["source"];

// Hidden by default: the dashboard focuses on calculations and the roadmap.
export const RESOURCES_PANEL_ENABLED = process.env.NEXT_PUBLIC_FENCE_DASHBOARD_RESOURCES === "true";

export default function ResourcesPanel() {
  const [resources, setResources] = useState<WorkspaceResourceResponse[]>([]);
  const [query, setQuery] = useState("");
  const [source, setSource] = useState<ResourceSource>("");
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setState("loading");
      try {
        const params = new URLSearchParams();
        if (query.trim()) params.set("q", query.trim());
        if (source) params.set("source", source);
        setResources(await apiRequest<WorkspaceResourceResponse[]>(`/api/workspace/resources?${params.toString()}`, {
          signal: controller.signal,
          authenticated: true,
        }));
        setState("ready");
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState("error");
      }
    }, 250);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [query, source]);

  return (
    <section className="ov-card ov-resources" aria-labelledby="ov-resources-title">
      <div className="ov-card-head">
        <h2 id="ov-resources-title">Resources</h2>
        <div className="ov-chips">
          {(["", "YouTube", "Public web"] as ResourceSource[]).map((item) => (
            <button key={item || "all"} type="button" className={`ov-chip ${source === item ? "is-active" : ""}`} onClick={() => setSource(item)}>
              {item || "All"}
            </button>
          ))}
        </div>
      </div>
      <input className="ov-search" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Find resources" aria-label="Search resources" />
      {state === "loading" && <p className="ov-muted">Loading resources…</p>}
      {state === "error" && <p className="ov-muted">Resources are temporarily unavailable.</p>}
      {state === "ready" && resources.length === 0 && <p className="ov-muted">No resources match these filters.</p>}
      {state === "ready" && (
        <ul className="ov-list">
          {resources.slice(0, 3).map((resource) => (
            <li key={resource.id}>
              <a href={resource.url} target="_blank" rel="noreferrer"><strong>{resource.title}</strong><span>{resource.source}</span></a>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
