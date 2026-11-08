"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Icon, Topography, WorkspacePageHeader } from "../../WorkspaceUI";
import { apiRequest } from "@/lib/api/client";
import { formatMoney, formatPercent } from "@/lib/api/decimal";
import type { SimulationProjectionResponse, SimulationScenarioResponse } from "@/lib/api/generated";
import { useWorkspaceAuth } from "@/components/auth/WorkspaceAuthGuard";
import SectionNav, { type SectionLink } from "./SectionNav";
import CalculationCharts from "./CalculationCharts";

type Scenario = SimulationScenarioResponse;
type Projection = SimulationProjectionResponse;
// suggested_adjustments is a free-form list on the backend; this is the shape the reviewer emits.
type SuggestedAdjustment = { field?: string; current_value?: string | null; suggested_value?: string | null; reason?: string };

// Cost lines in reading order: what you pay, what reduces it, then what you give up.
const COST_ORDER = [
  "tuition", "mandatory_fees", "additional_education", "incremental_living_cost", "gross_direct_cost",
  "scholarships_and_grants", "net_direct_cost", "baseline_income_during_study", "employment_income_during_study", "opportunity_cost",
];

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

const costLabels: Record<string, string> = {
  tuition: "Tuition", mandatory_fees: "Mandatory fees", additional_education: "Additional education",
  incremental_living_cost: "Incremental living costs", scholarships_and_grants: "Scholarships & grants",
  baseline_income_during_study: "Baseline income during study", employment_income_during_study: "Income during study",
  opportunity_cost: "Opportunity cost", gross_direct_cost: "Gross direct cost", net_direct_cost: "Net direct cost",
};

const scenarioLabels: Record<string, string> = { pessimistic: "Pessimistic", base: "Base", optimistic: "Optimistic" };
const scenarioSources: Record<string, string> = { pessimistic: "Market minimum", base: "Market median", optimistic: "Market maximum" };

const calculationSections: SectionLink[] = [
  { id: "summary", label: "Summary" },
  { id: "charts", label: "Charts" },
  { id: "scenarios", label: "Scenarios" },
  { id: "investment", label: "Investment" },
  { id: "assumptions", label: "Assumptions" },
  { id: "trajectory", label: "Salary trajectory" },
  { id: "evidence", label: "Evidence" },
  { id: "ai-review", label: "AI review" },
];

const calculationBreadcrumbs = [
  { label: "Workspace", href: "/workspace/overview" },
  { label: "Saved scenarios", href: "/workspace/scenarios" },
  { label: "Full calculation" },
];

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
        setProjection(projections[0] || null);
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

  const revision = scenario?.revisions.find((item) => item.revision_number === scenario.current_revision_number) || scenario?.revisions.at(-1);
  const assumptions = revision?.assumptions;
  const maximumSalary = useMemo(() => Math.max(1, ...(projection?.salary_trajectory || []).flatMap((point) => [point.target_salary, point.baseline_salary])), [projection]);
  const currency = projection?.currency || scenario?.currency || "USD";
  const money = (value: number | null | undefined) => formatMoney(value, currency);
  const barWidth = (value: number) => `${Math.max(0, value / maximumSalary * 100)}%`;
  const months = (value: number | null) => value == null ? "Not reached" : value < 24 ? `${value} months` : `${(value / 12).toFixed(1)} years`;

  if (loading) return <main className="sketch-page"><WorkspacePageHeader section="Full calculation" breadcrumbs={calculationBreadcrumbs} title="Full calculation" highlight="calculation" description="Investment, salary and payback details for your saved scenario." /><div className="workspace-status">Loading calculation…</div></main>;
  if (error || !scenario || !assumptions) return <main className="sketch-page"><WorkspacePageHeader section="Full calculation" breadcrumbs={calculationBreadcrumbs} title="Full calculation" highlight="calculation" description="Investment, salary and payback details for your saved scenario." /><div className="workspace-status is-error">{error || "This scenario has no readable revision."}</div><Link href="/workspace/scenarios" className="sketch-btn">← Back to saved scenarios</Link></main>;

  return <main className="sketch-page calculation-page">
    <WorkspacePageHeader
      section="Full calculation"
      breadcrumbs={calculationBreadcrumbs}
      title={scenario.name}
      highlight={scenario.name}
      description={`${assumptions.university} · ${assumptions.specialization} · ${assumptions.country}`}
    />
    <Link href="/workspace/scenarios" className="university-back">← Back to saved scenarios</Link>
    {projection ? <>
      <SectionNav sections={calculationSections} />
      <section id="summary" className="sketch-card sketch-card-dark calculation-hero"><Topography/><div className="calculation-hero-heading"><div><span className="sketch-chip is-active">Saved calculation</span><h2>Education investment forecast</h2><p>{scenario.target_role} · {projection.horizon_years}-year horizon · {projection.methodology_version}</p></div><span className={`calculation-confidence ${projection.unverified_assumptions.length ? "is-review" : ""}`}>{projection.unverified_assumptions.length ? "Review assumptions" : "Evidence attached"}</span></div><div className="calculation-kpis"><div><span>Total investment</span><strong>{money(projection.total_investment)}</strong><small>Direct cost + opportunity cost</small></div><div><span>Starting salary</span><strong>{money(projection.estimated_start_salary)}</strong><small>{projection.salary_basis.replaceAll("_", " ")}</small></div><div><span>Payback period</span><strong>{months(projection.payback_months)}</strong><small>{projection.break_even_reached ? "Break-even reached in horizon" : "Outside selected horizon"}</small></div><div><span>ROI</span><strong>{formatPercent(projection.roi_percent, "—")}</strong><small>{money(projection.cumulative_incremental_earnings)} cumulative gain</small></div></div>{projection.target_payback_years != null ? <PaybackVerdict projection={projection}/> : null}</section>
      <CalculationCharts projection={projection} money={money} />
      <section id="scenarios" className="sketch-card calculation-panel calculation-scenarios"><div className="calculation-panel-heading"><Icon name="tasks"/><div><h2>Scenarios</h2><p>The same costs and growth with the market minimum, median and maximum start salary.</p></div></div>
        {projection.scenario_outcomes.length ? <>
          <div className="scenario-outcomes">{projection.scenario_outcomes.map((item) => <article key={item.scenario} className={`scenario-outcome is-${item.scenario}`}>
            <header><strong>{scenarioLabels[item.scenario]}</strong><span>{projection.scenario_outcomes.length > 1 ? scenarioSources[item.scenario] : "Your salary input"}</span></header>
            <dl>
              <div><dt>Start salary</dt><dd>{money(item.start_salary)}</dd></div>
              <div><dt>ROI</dt><dd>{formatPercent(item.roi_percent, "—")}</dd></div>
              <div><dt>Payback</dt><dd>{months(item.payback_months)}</dd></div>
              <div><dt>NPV</dt><dd>{item.npv == null ? "—" : money(item.npv)}</dd></div>
            </dl>
          </article>)}</div>
          <p className="calculation-note">{projection.scenario_outcomes.length === 1 ? "Pessimistic and optimistic cases need a market salary snapshot; this forecast uses a salary you entered. " : ""}{projection.calculation_inputs.discount_rate_percent == null ? "NPV is shown only when a discount rate is set." : `NPV discounts each year at ${projection.calculation_inputs.discount_rate_percent}% from the start of study.`}{projection.calculation_inputs.inflation_percent != null ? ` Amounts are in today's money at ${projection.calculation_inputs.inflation_percent}% inflation.` : " Amounts are nominal (no inflation applied)."}{projection.calculation_inputs.job_search_months ? ` First year assumes ${projection.calculation_inputs.job_search_months} months of job search.` : ""}{projection.calculation_inputs.employment_probability_percent != null && projection.calculation_inputs.employment_probability_percent < 100 ? ` Income is weighted by a ${projection.calculation_inputs.employment_probability_percent}% chance of a job in the field.` : ""}</p>
        </> : <p className="calculation-note">This calculation was made with {projection.methodology_version}, before scenario ranges existed. Create a new calculation to see them.</p>}
      </section>
      <div className="calculation-grid"><section id="investment" className="sketch-card calculation-panel"><div className="calculation-panel-heading"><Icon name="database"/><div><h2>Investment breakdown</h2><p>How the total investment is composed.</p></div></div><div className="calculation-lines">{Object.entries(projection.cost_breakdown).filter(([, value]) => value != null).sort(([a], [b]) => (COST_ORDER.indexOf(a) + 1 || 99) - (COST_ORDER.indexOf(b) + 1 || 99)).map(([key, value]) => <div key={key}><span>{costLabels[key] || key.replaceAll("_", " ")}</span><strong>{money(value)}</strong></div>)}<div className="is-total"><span>Total investment</span><strong>{money(projection.total_investment)}</strong></div></div></section>
        <section id="assumptions" className="sketch-card calculation-panel"><div className="calculation-panel-heading"><Icon name="graduation"/><div><h2>Scenario assumptions</h2><p>The education and career inputs saved in revision {revision.revision_number}.</p></div></div><dl className="calculation-assumptions"><div><dt>University</dt><dd>{assumptions.university}</dd></div><div><dt>Programme</dt><dd>{assumptions.specialization}</dd></div><div><dt>Degree</dt><dd>{assumptions.degree}</dd></div><div><dt>Study duration</dt><dd>{assumptions.study_duration_years} years</dd></div><div><dt>Annual tuition</dt><dd>{money(assumptions.annual_tuition)}</dd></div><div><dt>Career target</dt><dd>{assumptions.career_target}</dd></div><div><dt>Experience</dt><dd>{assumptions.experience_years} years</dd></div><div><dt>Current skills</dt><dd>{assumptions.existing_skills.length ? assumptions.existing_skills.join(", ") : "Not provided"}</dd></div></dl></section>
        <section id="trajectory" className="sketch-card calculation-panel calculation-trajectory"><div className="calculation-panel-heading"><Icon name="tasks"/><div><h2>Salary trajectory</h2><p>Target salary versus the baseline over time.</p></div></div><div className="trajectory-table"><div className="trajectory-head"><span>Year</span><span>Salary comparison</span><span>Incremental gain</span></div>{projection.salary_trajectory.map((point) => <div className="trajectory-row" key={point.year}><strong>{point.year}</strong><div className="trajectory-bars"><i className="is-target" style={{ width: barWidth(point.target_salary) }}><span>{money(point.target_salary)}</span></i><i className="is-baseline" style={{ width: barWidth(point.baseline_salary) }}><span>{money(point.baseline_salary)}</span></i></div><strong>{money(point.incremental_earnings)}</strong></div>)}</div></section>
        <section id="evidence" className="sketch-card calculation-panel"><div className="calculation-panel-heading"><Icon name="info"/><div><h2>Evidence & methodology</h2><p>Sources and limitations behind this result.</p></div></div><div className="calculation-method"><div><span>Methodology</span><strong>{projection.methodology_version}</strong></div><div><span>Calculation date</span><strong>{new Date(projection.created_at).toLocaleDateString()}</strong></div><div><span>Source snapshots</span><strong>{projection.source_snapshot_refs.length || revision.source_snapshot_refs.length}</strong></div></div>{projection.evidence.length ? <div className="calculation-evidence">{projection.evidence.map((item, index) => <article key={`${item.metric}-${index}`}><div><strong>{item.source_name}</strong><span>{item.metric.replaceAll("_", " ")} · {item.confidence} confidence</span></div><small>{item.source_reference}</small></article>)}</div> : <div className="university-empty">No detailed evidence records are attached to this calculation.</div>}{projection.unverified_assumptions.length > 0 && <div className="calculation-warnings"><strong>Assumptions requiring review</strong><ul>{projection.unverified_assumptions.map((item) => <li key={item}>{warningLabels[item] || item.replaceAll("_", " ")}</li>)}</ul></div>}</section>
        <section id="ai-review" className="sketch-card sketch-card-violet calculation-panel calculation-ai-review" aria-live="polite"><div className="calculation-panel-heading"><Icon name="info"/><div><h2>AI review</h2><p>An advisory second opinion. It never changes the numbers above.</p></div></div>
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
              {projection.ai_review.suggested_adjustments.length > 0 && <div className="calculation-warnings"><strong>Suggested adjustments (apply via a new revision)</strong><ul>{(projection.ai_review.suggested_adjustments as SuggestedAdjustment[]).map((item, index) => <li key={index}><b>{item.field}</b>: {item.current_value ?? "—"} → {item.suggested_value ?? "—"}. {item.reason}</li>)}</ul></div>}
              <div className="ai-review-footer"><small>{projection.ai_review.provider_model}{projection.ai_review.completed_at ? ` · ${new Date(projection.ai_review.completed_at).toLocaleString()}` : ""}</small><button type="button" className="sketch-btn" onClick={runReview} disabled={reviewBusy}>{reviewBusy ? "Starting…" : "Run again"}</button></div>
            </div>}
          {reviewError && <p className="ai-review-error" role="alert">{reviewError}</p>}
        </section>
      </div>
    </> : <section className="sketch-card sketch-card-violet calculation-empty"><Icon name="info" size={34}/><div><h2>Scenario saved without a projection</h2><p>The education assumptions are stored, but a financial projection was not created. Create a new scenario when validated salary data is available.</p><Link href="/workspace/scenario/new" className="sketch-btn sketch-btn-primary">Create calculation <Icon name="arrow" size={17}/></Link></div></section>}
    <div className="calculation-actions"><Link href="/workspace/compare" className="sketch-btn">Compare universities <Icon name="arrow" size={17}/></Link>{isAdmin && <Link href={`/workspace/roadmap/simulation?target=${encodeURIComponent(assumptions.career_target)}`} className="sketch-btn sketch-btn-primary">Build career roadmap <Icon name="arrow" size={17}/></Link>}</div>
  </main>;
}
