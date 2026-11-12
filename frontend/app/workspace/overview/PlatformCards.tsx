"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { formatMoney } from "@/lib/api/decimal";
import type { MarketNewsResponse, SimulationProjectionExplainabilityResponse } from "@/lib/api/generated";
import { workspaceFetch, type WorkspaceConnection } from "@/lib/api/workspace";

const PLATFORMS: Array<{ id: string; name: string; logo: string }> = [
  { id: "linkedin", name: "LinkedIn", logo: "in" },
  { id: "github", name: "GitHub", logo: "GH" },
  { id: "youtube", name: "YouTube", logo: "▶" },
];

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

/** Latest labour-market headlines for a role and country, straight from the public news feed. */
function MarketNews({ role, country }: { role: string; country: string }) {
  const [news, setNews] = useState<MarketNewsResponse | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({ role, country });
    workspaceFetch<MarketNewsResponse>(`/api/market/news?${params}`, { signal: controller.signal })
      .then(setNews)
      .catch((reason) => { if (reason.name !== "AbortError") setFailed(true); });
    return () => controller.abort();
  }, [role, country]);

  if (failed) return <p className="ov-muted">Market news is temporarily unavailable.</p>;
  if (!news) return <p className="ov-muted">Loading market news…</p>;
  if (!news.items.length) return <p className="ov-muted">No recent news for “{news.query}”.</p>;
  return (
    <div className="ov-news">
      <h3>Market news · {role} in {country}</h3>
      <ul>
        {news.items.slice(0, 4).map((item) => (
          <li key={item.url}>
            <a href={item.url} target="_blank" rel="noreferrer">{item.title}</a>
            <small>{[item.source, item.published_at ? formatDate(item.published_at) : ""].filter(Boolean).join(" · ")}</small>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Salary market data behind the latest forecast, with its sources. Shows nothing invented when no snapshot was used. */
export function MarketCard({ explainability, role, country }: { explainability: SimulationProjectionExplainabilityResponse | null | undefined; role?: string | null; country?: string | null }) {
  const provenance = explainability?.source_snapshots[0];
  const snapshot = provenance?.snapshot;
  const newsRole = snapshot?.role || role;
  const newsCountry = snapshot?.country || country;
  return (
    <section className="ov-card ov-market" aria-labelledby="ov-market-title">
      <div className="ov-card-head">
        <h2 id="ov-market-title">Job market</h2>
        {snapshot && <span className="ov-pill">{snapshot.confidence} confidence</span>}
      </div>
      {snapshot ? (
        <>
          <p className="ov-market-role">{snapshot.role} · {snapshot.country} · {snapshot.seniority}</p>
          <dl className="ov-market-stats">
            <div><dt>Median salary</dt><dd>{formatMoney(snapshot.median_salary, snapshot.currency)}</dd></div>
            <div><dt>Range</dt><dd>{formatMoney(snapshot.salary_min, snapshot.currency)} – {formatMoney(snapshot.salary_max, snapshot.currency)}</dd></div>
            <div><dt>Open vacancies</dt><dd>{snapshot.vacancy_count?.toLocaleString("en-GB") ?? "—"}</dd></div>
            <div><dt>Demand index</dt><dd>{snapshot.demand_index ?? "—"}</dd></div>
          </dl>
          <ul className="ov-sources">
            {snapshot.sources.map((source) => (
              <li key={`${source.name}-${source.reference}`}>
                {source.url ? <a href={source.url} target="_blank" rel="noreferrer">{source.name} ↗</a> : <span>{source.name}</span>}
                <small>collected {formatDate(source.acquired_at)}</small>
              </li>
            ))}
          </ul>
          <p className="ov-muted">Snapshot from {formatDate(snapshot.snapshot_date)}{provenance && provenance.age_days > 0 ? `, ${provenance.age_days} days old` : ""}. Salary per year, {snapshot.salary_basis}.</p>
        </>
      ) : explainability ? (
        <p className="ov-muted">Your latest forecast uses salary figures you entered yourself, so there is no market snapshot to show.</p>
      ) : (
        <div className="ov-empty">
          <p><strong>No market data yet.</strong> Compute a forecast and Fence will show the salary range, vacancies and sources it used.</p>
          <Link href="/workspace/scenarios" className="ov-link">Open calculations →</Link>
        </div>
      )}
      {newsRole && newsCountry ? <MarketNews role={newsRole} country={newsCountry} /> : null}
    </section>
  );
}

/** External platforms. Integrations show their real status, never a fake connection. */
export function PlatformsCard({ connections }: { connections: Record<string, WorkspaceConnection> }) {
  return (
    <section className="ov-card ov-platforms" aria-labelledby="ov-platforms-title">
      <div className="ov-card-head">
        <h2 id="ov-platforms-title">Platforms</h2>
        <Link href="/workspace/settings" className="ov-link">Manage →</Link>
      </div>
      <ul className="ov-platform-list">
        {PLATFORMS.map((platform) => {
          const connection = connections[platform.id];
          const status = connection?.connected ? "Connected" : connection?.available ? "Not connected" : "Not configured";
          return (
            <li key={platform.id}>
              <span className="ov-platform-logo" aria-hidden="true">{platform.logo}</span>
              <span><strong>{platform.name}</strong><small>{connection?.label || "Integration not configured"}</small></span>
              <em className={connection?.connected ? "is-on" : ""}>{status}</em>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
