"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { Icon, Topography, WorkspacePageHeader } from "../../WorkspaceUI";
import { apiRequest } from "@/lib/api/client";
import { formatMoney, formatPercent, formatRoiPerYear } from "@/lib/api/decimal";
import { foldRail } from "@/lib/railState";
import type { SimulationProjectionResponse, SimulationScenarioListItem, SimulationScenarioResponse } from "@/lib/api/generated";
import { useWorkspaceAuth } from "@/components/auth/WorkspaceAuthGuard";
import SectionNav, { type SectionLink } from "./SectionNav";
import CalculationCharts from "./CalculationCharts";
import CostEditor, { useCostLines } from "./CostEditor";
import { parseDecimal } from "../../DecimalInput";
import "../../../styles/calculation-split.css";

type Scenario = SimulationScenarioResponse;
type Projection = SimulationProjectionResponse;
// suggested_adjustments is a free-form list on the backend; this is the shape the reviewer emits.
type SuggestedAdjustment = { field?: string; current_value?: string | null; suggested_value?: string | null; reason?: string };

const warningLabels: Record<string, string> = {
  annual_tuition: "Tuition has no verified source",
  estimated_start_salary: "Starting salary has no verified source",
  salary_growth: "Salary growth is your own assumption",
  mandatory_fees: "Mandatory fees have no verified source",
  scholarships_and_grants: "Scholarships have no verified source",
  employment_income_during_study: "Income during study has no verified source",
  inflation: "Inflation rate is your own assumption",
  inflation_not_applied: "Inflation not applied: amounts are nominal, not today's money",
};

const scenarioLabels: Record<string, string> = { pessimistic: "Pessimistic", base: "Base", optimistic: "Optimistic" };
const scenarioSources: Record<string, string> = { pessimistic: "Market minimum", base: "Market median", optimistic: "Market maximum" };

const calculationSections: SectionLink[] = [
  { id: "summary", label: "Summary" },
  { id: "investment", label: "Costs" },
  { id: "charts", label: "Charts" },
  { id: "scenarios", label: "Scenarios" },
  { id: "assumptions", label: "Assumptions" },
  { id: "evidence", label: "Sources" },
  { id: "trajectory", label: "Salary trajectory" },
  { id: "ai-review", label: "AI review" },
];

const calculationBreadcrumbs = [
  { label: "Workspace", href: "/workspace/overview" },
  { label: "Saved scenarios", href: "/workspace/scenarios" },
  { label: "Full calculation" },
];

/** The person's calculations down the side: any of them opens in this same view. */
function CalculationList({ currentId }: { currentId: string }) {
  const [items, setItems] = useState<SimulationScenarioListItem[] | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    apiRequest<SimulationScenarioListItem[]>("/api/simulations", { signal: controller.signal, authenticated: true })
      .then(setItems)
      .catch((reason) => { if (reason.name !== "AbortError") setItems([]); });
    return () => controller.abort();
  }, []);
  const months = (value: number | null | undefined) => value == null ? "No payback" : value < 24 ? `${value} mo` : `${(value / 12).toFixed(1)} yrs`;
  const nav = useRef<HTMLElement>(null);
  // On a phone the list scrolls sideways: keep the open calculation in sight.
  useEffect(() => {
    const list = nav.current;
    const current = list?.querySelector<HTMLElement>(".is-current");
    if (list && current) list.scrollTo({ left: current.offsetLeft - list.offsetLeft, top: current.offsetTop - list.offsetTop - 60 });
  }, [items, currentId]);
  return (
    <nav ref={nav} className="calc-list" aria-label="Your calculations">
      <Link href="/workspace/scenario/new" className="calc-list-new"><span aria-hidden="true">+</span> New calculation</Link>
      {items === null ? <p className="calc-list-note">Loading…</p> : null}
      {items?.map((item) => (
        <Link key={item.id} href={`/workspace/scenarios/${item.id}`} aria-current={String(item.id) === currentId ? "page" : undefined}
          className={`calc-list-item ${String(item.id) === currentId ? "is-current" : ""}`}>
          <strong>{item.target_role || item.name}</strong>
          <span>{[item.specialization, item.university].filter(Boolean).join(" · ") || item.country}</span>
          <small>{item.projection_id ? `ROI ${formatRoiPerYear(item.roi_percent)} · ${months(item.payback_months)}` : "No forecast yet"}</small>
        </Link>
      ))}
    </nav>
  );
}

function PaybackVerdict({ projection }: { projection: Projection }) {
  const target = projection.target_payback_years;
  const gap = projection.payback_target_gap_months;
  const met = projection.payback_within_target === true;
  const span = (value: number) => value === 1 ? "1 month" : `${value} months`;
  const detail = met
    ? gap != null && gap < 0 ? `${span(-gap)} ahead of the target` : "right on the target"
    : gap != null ? `${span(gap)} later than the target` : `no payback within the ${projection.horizon_years}-year horizon`;
  return (
    <div className={`payback-verdict ${met ? "is-met" : "is-missed"}`} role="status">
      <span className="payback-verdict-badge">{met ? "Yes" : "No"}</span>
      <p><strong>Pays back within {target} {target === 1 ? "year" : "years"} after graduation?</strong> {detail}.</p>
    </div>
  );
}

export default function CalculationDetailsPage() {
  const isAdmin = useWorkspaceAuth().user.is_admin;
  const params = useParams<{ id: string }>();
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [projection, setProjection] = useState<Projection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reviewBusy, setReviewBusy] = useState(false);
  const [reviewError, setReviewError] = useState("");

  // List on the left, calculation on the right: the workspace rail folds to make room.
  useEffect(() => foldRail(), []);

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      setLoading(true); setError("");
      try {
        const scenarioData = await apiRequest<Scenario>(`/api/simulations/${params.id}`, {
          signal: controller.signal,
          authenticated: true,
          fallbackMessage: "Could not load this scenario.",
        });
        setScenario(scenarioData);
        const projections = await apiRequest<Projection[]>(`/api/simulations/${params.id}/revisions/${scenarioData.current_revision_number}/projections`, {
          signal: controller.signal,
          authenticated: true,
          fallbackMessage: "Could not load the saved calculation.",
        });
        // A link may point at one saved version; otherwise the newest.
        const wanted = Number(new URLSearchParams(window.location.search).get("projection"));
        setProjection(projections.find((item) => item.id === wanted) || projections[0] || null);
      } catch (reason) {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : "Could not load the calculation.");
      } finally { setLoading(false); }
    }
    void load();
    return () => controller.abort();
  }, [params.id]);

  const reviewStatus = projection?.ai_review?.status;
  const reviewInFlight = reviewStatus === "pending" || reviewStatus === "running";

  // The review runs in a background worker; poll until it settles (max ~3 minutes).
  useEffect(() => {
    if (!scenario || !projection || !reviewInFlight) return;
    let attempts = 0;
    const timer = window.setInterval(async () => {
      attempts += 1;
      try {
        const projections = await apiRequest<Projection[]>(`/api/simulations/${scenario.id}/revisions/${scenario.current_revision_number}/projections`, {
          authenticated: true,
          fallbackMessage: "Could not refresh the AI review.",
        });
        const latest = projections.find((item) => item.id === projection.id);
        if (latest) setProjection(latest);
      } catch { /* keep the last known state; the next tick retries */ }
      if (attempts >= 45) window.clearInterval(timer);
    }, 4000);
    return () => window.clearInterval(timer);
  }, [scenario, projection?.id, reviewInFlight]); // eslint-disable-line react-hooks/exhaustive-deps

  async function runReview() {
    if (!scenario || !projection) return;
    setReviewBusy(true); setReviewError("");
    try {
      const updated = await apiRequest<Projection>(`/api/simulations/${scenario.id}/revisions/${scenario.current_revision_number}/projections/${projection.id}/ai-review`, {
        method: "POST",
        authenticated: true,
        fallbackMessage: "Could not start the AI review.",
      });
      setProjection(updated);
    } catch (reason) {
      setReviewError(reason instanceof Error ? reason.message : "Could not start the AI review.");
    } finally { setReviewBusy(false); }
  }

  const costEditor = useCostLines(
    scenario && projection ? `/api/simulations/${scenario.id}/revisions/${scenario.current_revision_number}/projections/${projection.id}` : null,
    projection,
    (saved) => {
      setProjection(saved);
      window.history.replaceState(window.history.state, "", `?projection=${saved.id}`);
    },
  );

  const revision = scenario?.revisions.find((item) => item.revision_number === scenario.current_revision_number) || scenario?.revisions.at(-1);
  const assumptions = revision?.assumptions;
  // Everything on the page reads this: the saved result, or the preview of the changed cost lines.
  const view: Projection | null = projection && costEditor.preview ? { ...projection, ...costEditor.preview } : projection;
  const maximumSalary = useMemo(() => Math.max(1, ...(view?.salary_trajectory || []).flatMap((point) => [point.target_salary, point.baseline_salary])), [view]);
  const currency = projection?.currency || scenario?.currency || "USD";
  const money = (value: number | null | undefined) => formatMoney(value, currency);
  const barWidth = (value: number) => `${Math.max(0, value / maximumSalary * 100)}%`;
  const months = (value: number | null) => value == null ? "Not reached" : value < 24 ? `${value} months` : `${(value / 12).toFixed(1)} years`;

  if (loading) return <main className="sketch-page"><WorkspacePageHeader section="Full calculation" breadcrumbs={calculationBreadcrumbs} title="Full calculation" highlight="calculation" description="Investment, salary and payback details for your saved scenario." /><div className="workspace-status">Loading calculation…</div></main>;
  if (error || !scenario || !assumptions) return <main className="sketch-page"><WorkspacePageHeader section="Full calculation" breadcrumbs={calculationBreadcrumbs} title="Full calculation" highlight="calculation" description="Investment, salary and payback details for your saved scenario." /><div className="workspace-status is-error">{error || "This scenario has no readable revision."}</div><Link href="/workspace/scenarios" className="sketch-btn">← Back to saved scenarios</Link></main>;

  const inputs = view?.calculation_inputs;
  const trainingAdvice = (projection?.ai_review?.suggested_adjustments as SuggestedAdjustment[] | undefined)?.find((item) => item.field === "additional_training");
  const trainingCost = trainingAdvice?.suggested_value ? parseDecimal(trainingAdvice.suggested_value) : null;
  const trainingLine = costEditor.lines.find((line) => line.key === "additional_training");

  return <main className="sketch-page calculation-page">
    <WorkspacePageHeader
      section="Full calculation"
      breadcrumbs={calculationBreadcrumbs}
      title={scenario.name}
      highlight={scenario.name}
      description={[assumptions.university, assumptions.specialization, assumptions.country].filter(Boolean).join(" · ")}
    />
    <div className="calc-split">
    <CalculationList currentId={params.id} />
    <div className="calc-detail">
    {projection && view && inputs ? <>
      <SectionNav sections={calculationSections} />
      <section id="summary" className="sketch-card sketch-card-dark calculation-hero"><Topography/><div className="calculation-hero-heading"><div><span className="sketch-chip is-active">{costEditor.preview ? "Preview, not saved" : "Saved calculation"}</span><h2>Education investment forecast</h2><p>{scenario.target_role} · {view.horizon_years}-year horizon</p></div><span className={`calculation-confidence ${view.unverified_assumptions.length ? "is-review" : ""}`}>{view.unverified_assumptions.length ? "Review assumptions" : "Evidence attached"}</span></div><div className="calculation-kpis"><div><span>Total investment</span><strong>{money(view.total_investment)}</strong><small>Direct cost + pay given up</small></div><div><span>Starting salary</span><strong>{money(view.estimated_start_salary)}</strong><small>{view.salary_basis.replaceAll("_", " ")}</small></div><div><span>Payback period</span><strong>{months(view.payback_months)}</strong><small>{view.break_even_reached ? "Break-even reached in horizon" : "Outside selected horizon"}</small></div><div><span>ROI a year</span><strong>{formatRoiPerYear(view.roi_percent, view.horizon_years)}</strong><small>{formatPercent(view.roi_percent, "—")} over {view.horizon_years} years · {money(view.cumulative_incremental_earnings)} extra earned</small></div></div>{view.target_payback_years != null ? <PaybackVerdict projection={view}/> : null}</section>
      <CostEditor editor={costEditor} years={assumptions.study_duration_years} currency={currency} money={money} costs={view.cost_breakdown} total={view.total_investment} />
      <CalculationCharts projection={view} money={money} lines={costEditor.lines} />
      <section id="scenarios" className="sketch-card calculation-panel calculation-scenarios"><div className="calculation-panel-heading"><Icon name="tasks"/><div><h2>Scenarios</h2><p>The same costs with the lowest, middle and highest starting salary on the market.</p></div></div>
        {view.scenario_outcomes.length ? <>
          <div className="scenario-outcomes">{view.scenario_outcomes.map((item) => <article key={item.scenario} className={`scenario-outcome is-${item.scenario}`}>
            <header><strong>{scenarioLabels[item.scenario]}</strong><span>{view.scenario_outcomes.length > 1 ? scenarioSources[item.scenario] : "Your salary input"}</span></header>
            <dl>
              <div><dt>Start salary</dt><dd>{money(item.start_salary)}</dd></div>
              <div><dt>ROI a year</dt><dd>{formatRoiPerYear(item.roi_percent, view.horizon_years)}</dd></div>
              <div><dt>Payback</dt><dd>{months(item.payback_months)}</dd></div>
              <div><dt>NPV</dt><dd>{item.npv == null ? "—" : money(item.npv)}</dd></div>
            </dl>
          </article>)}</div>
          <p className="calculation-note">{view.scenario_outcomes.length === 1 ? "Lowest and highest cases need market salary data; this forecast uses a salary you entered. " : ""}{inputs.discount_rate_percent == null ? "NPV is shown only when a discount rate is set." : `NPV is what all the extra earnings minus the investment are worth in today's money, discounted at ${inputs.discount_rate_percent}% a year. Above zero means studying beats keeping the money at that rate.`}</p>
        </> : <p className="calculation-note">This calculation is older than scenario ranges. Create a new calculation to see them.</p>}
      </section>
      <div className="calculation-grid">
        <section id="assumptions" className="sketch-card calculation-panel"><div className="calculation-panel-heading"><Icon name="graduation"/><div><h2>Assumptions</h2><p>What you told us, and what Fence worked out for you.</p></div></div><dl className="calculation-assumptions"><div><dt>University</dt><dd>{assumptions.university || "Not chosen yet"}</dd></div><div><dt>Programme</dt><dd>{assumptions.specialization || "Not chosen yet"}</dd></div><div><dt>Degree</dt><dd>{assumptions.degree}</dd></div><div><dt>Study years</dt><dd>{assumptions.study_duration_years}</dd></div><div><dt>Career target</dt><dd>{assumptions.career_target}</dd></div><div><dt>Experience</dt><dd>{assumptions.experience_years} years</dd></div><div><dt>Inflation</dt><dd>{inputs.inflation_percent == null ? "Not applied" : `${inputs.inflation_percent}% a year`}</dd></div><div><dt>Chance of a job in the field</dt><dd>{inputs.employment_probability_percent ?? 100}%</dd></div><div><dt>Job search</dt><dd>{inputs.job_search_months ?? 0} months</dd></div><div><dt>Income without this degree</dt><dd>{money(inputs.baseline_annual_salary)} a year</dd></div></dl></section>
        <section id="evidence" className="sketch-card calculation-panel"><div className="calculation-panel-heading"><Icon name="info"/><div><h2>Sources</h2><p>Where the numbers come from.</p></div></div>{projection.evidence.length ? <div className="calculation-evidence">{projection.evidence.map((item, index) => <article key={`${item.metric}-${index}`}><div>{/^https?:/.test(item.source_reference) ? <a href={item.source_reference} target="_blank" rel="noreferrer"><strong>{item.source_name}</strong></a> : <strong>{item.source_name}</strong>}<span>{item.metric.replaceAll("_", " ")} · {item.confidence} confidence</span></div></article>)}</div> : <div className="university-empty">No sources are attached to this calculation.</div>}{view.unverified_assumptions.length > 0 && <div className="calculation-warnings"><strong>Assumptions requiring review</strong><ul>{view.unverified_assumptions.map((item) => <li key={item}>{warningLabels[item] || item.replaceAll("_", " ")}</li>)}</ul></div>}</section>
        <section id="trajectory" className="sketch-card calculation-panel calculation-trajectory"><div className="calculation-panel-heading"><Icon name="tasks"/><div><h2>Salary trajectory</h2><p>Target salary versus the baseline over time.</p></div></div><div className="trajectory-table"><div className="trajectory-head"><span>Year</span><span>Salary comparison</span><span>Incremental gain</span></div>{view.salary_trajectory.map((point) => <div className="trajectory-row" key={point.year}><strong>{point.year}</strong><div className="trajectory-bars"><i className="is-target" style={{ width: barWidth(point.target_salary) }}><span>{money(point.target_salary)}</span></i><i className="is-baseline" style={{ width: barWidth(point.baseline_salary) }}><span>{money(point.baseline_salary)}</span></i></div><strong>{money(point.incremental_earnings)}</strong></div>)}</div></section>
        <section id="ai-review" className="sketch-card sketch-card-violet calculation-panel calculation-ai-review" aria-live="polite"><div className="calculation-panel-heading"><Icon name="info"/><div><h2>AI review</h2><p>An overall opinion on this decision. It changes the numbers only if you add its estimate yourself.</p></div></div>
          {!projection.ai_review || projection.ai_review.status === "not_configured" ? <div className="ai-review-state"><p>AI review is not enabled on this server{projection.ai_review?.error_message ? ` (${projection.ai_review.error_message})` : ""}.</p></div>
          : reviewInFlight ? <div className="ai-review-state"><span className="ai-review-pulse" aria-hidden="true"/><p>{reviewStatus === "running" ? "The reviewer is checking this calculation…" : "Review queued…"}</p></div>
          : projection.ai_review.status === "failed" ? <div className="ai-review-state is-error"><p>The review could not be completed.{projection.ai_review.error_message ? ` ${projection.ai_review.error_message.slice(0, 240)}` : ""}</p><button type="button" className="sketch-btn" onClick={runReview} disabled={reviewBusy}>{reviewBusy ? "Starting…" : "Try again"}</button></div>
          : <div className="ai-review-body">
              <div className="calculation-method"><div><span>Calculation check</span><strong>{projection.ai_review.calculation_consistent ? "Consistent" : "Inconsistencies found"}</strong></div><div><span>Confidence</span><strong>{projection.ai_review.confidence_score == null ? "—" : `${Math.round(projection.ai_review.confidence_score)}/100`}</strong></div><div><span>Career risk</span><strong>{projection.ai_review.ai_risk_score == null ? "—" : `${projection.ai_review.ai_risk_score}/100`}</strong></div></div>
              {projection.ai_review.verdict && <p className="ai-review-verdict">{projection.ai_review.verdict}</p>}
              {projection.ai_review.prediction_summary && <p className="ai-review-summary">{projection.ai_review.prediction_summary}</p>}
              <div className="ai-review-lists">
                {projection.ai_review.recommendations.length > 0 && <div><strong>Recommendations</strong><ul>{projection.ai_review.recommendations.map((item, index) => <li key={index}>{item}</li>)}</ul></div>}
                {projection.ai_review.risks.length > 0 && <div><strong>Risks</strong><ul>{projection.ai_review.risks.map((item, index) => <li key={index}>{item}</li>)}</ul></div>}
              </div>
              {trainingCost != null && !Number.isNaN(trainingCost) && trainingCost > 0 && trainingLine ? <div className="ai-training-offer"><p><strong>Training this career usually needs: about {money(trainingCost)}.</strong> {trainingAdvice?.reason}</p>{trainingLine.enabled && trainingLine.amount === trainingCost ? <span>Added to your costs</span> : <button type="button" className="sketch-btn sketch-btn-primary" onClick={() => costEditor.change("additional_training", { amount: trainingCost, enabled: true, source: "ai", source_name: null, source_url: null })}>Add to costs</button>}</div> : null}
              {projection.ai_review.suggested_adjustments.length > 0 && <div className="calculation-warnings"><strong>Suggested adjustments</strong><ul>{(projection.ai_review.suggested_adjustments as SuggestedAdjustment[]).filter((item) => item.field !== "additional_training").map((item, index) => <li key={index}><b>{item.field}</b>: {item.current_value ?? "—"} → {item.suggested_value ?? "—"}. {item.reason}</li>)}</ul></div>}
              <div className="ai-review-footer"><small>{projection.ai_review.provider_model}{projection.ai_review.completed_at ? ` · ${new Date(projection.ai_review.completed_at).toLocaleString()}` : ""}</small><button type="button" className="sketch-btn" onClick={runReview} disabled={reviewBusy}>{reviewBusy ? "Starting…" : "Run again"}</button></div>
            </div>}
          {reviewError && <p className="ai-review-error" role="alert">{reviewError}</p>}
        </section>
      </div>
    </> : <section className="sketch-card sketch-card-violet calculation-empty"><Icon name="info" size={34}/><div><h2>Scenario saved without a projection</h2><p>The education assumptions are stored, but a financial projection was not created. Create a new scenario when validated salary data is available.</p><Link href="/workspace/scenario/new" className="sketch-btn sketch-btn-primary">Create calculation <Icon name="arrow" size={17}/></Link></div></section>}
    <div className="calculation-actions"><Link href="/workspace/compare" className="sketch-btn">Compare universities <Icon name="arrow" size={17}/></Link>{isAdmin && <Link href={`/workspace/roadmap/simulation?target=${encodeURIComponent(assumptions.career_target)}`} className="sketch-btn sketch-btn-primary">Build career roadmap <Icon name="arrow" size={17}/></Link>}</div>
    </div>
    </div>
  </main>;
}
