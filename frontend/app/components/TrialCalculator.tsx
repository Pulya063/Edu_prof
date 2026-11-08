"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ApiRequestError, fieldError, type FieldErrors } from "@/lib/api/client";
import "../styles/trial.css";
import { getTrialOptions, runTrialProjection, type TrialProjectionOption, type TrialProjectionResponse } from "@/lib/api/trial";

/* Trial calculation for visitors without an account. Every number on screen comes from the
   server's deterministic engine (/api/roi/preview); this component only collects inputs and
   formats the response. */

const TARGETS = [3, 4, 5, 10] as const;
const SCENARIO_LABEL = { pessimistic: "Pessimistic", base: "Base", optimistic: "Optimistic" } as const;
const SOURCE_LABEL: Record<string, string> = { target_start_salary: "Starting salary", baseline_salary: "Pay without the degree", inflation: "Inflation" };

const SOURCE_HINT = (option: TrialProjectionOption) =>
  option.salary_source === "official"
    ? "Salary estimated from Eurostat's official earnings survey (people under 30 in this occupation group): there are too few junior adverts right now."
    : option.seniority === "junior"
      ? "Salary from current junior adverts and salary surveys."
      : "Salary from current adverts for all experience levels: too few junior adverts publish a salary.";

const money = (value: number, currency: string) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency, maximumFractionDigits: 0 }).format(value);
const amount = (value: number) => new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
const months = (value: number | null) => (value === null ? "Not within 10 years" : `${value} mo · ${(value / 12).toFixed(1)} yrs`);

export default function TrialCalculator() {
  const [options, setOptions] = useState<TrialProjectionOption[] | null>(null);
  const [optionsError, setOptionsError] = useState("");
  const [country, setCountry] = useState("");
  const [role, setRole] = useState("");
  const [university, setUniversity] = useState("");
  const [studyYears, setStudyYears] = useState(4);
  const [tuition, setTuition] = useState("0");
  const [search, setSearch] = useState(3);
  const [target, setTarget] = useState<number | null>(4);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [result, setResult] = useState<TrialProjectionResponse | null>(null);

  useEffect(() => {
    getTrialOptions()
      .then((items) => {
        setOptions(items);
        if (items[0]) { setCountry(items[0].country); setRole(items[0].career_target); }
      })
      .catch((reason: unknown) => setOptionsError(reason instanceof Error ? reason.message : "Could not load the available professions."));
  }, []);

  const countries = useMemo(() => Array.from(new Set((options ?? []).map((item) => item.country))), [options]);
  const roles = useMemo(() => (options ?? []).filter((item) => item.country === country), [options, country]);
  const currency = roles[0]?.currency ?? "PLN";
  const selectedRole = roles.find((item) => item.career_target === role);

  const chooseCountry = (value: string) => {
    setCountry(value); setResult(null);
    const first = (options ?? []).find((item) => item.country === value);
    if (first && !(options ?? []).some((item) => item.country === value && item.career_target === role)) setRole(first.career_target);
  };

  const calculate = async () => {
    setBusy(true); setError(""); setFieldErrors({});
    try {
      setResult(await runTrialProjection({
        country: country as "Poland" | "Ukraine", career_target: role, university: university.trim() || null,
        study_years: studyYears, annual_tuition: Number(tuition) || 0, job_search_months: search, target_payback_years: target,
      }));
    } catch (reason) {
      if (reason instanceof ApiRequestError) { setFieldErrors(reason.fieldErrors); setError(reason.message); }
      else setError("Could not calculate this scenario.");
    } finally {
      setBusy(false);
    }
  };

  if (optionsError) return <p className="tc-notice" role="alert">{optionsError}</p>;
  if (options === null) return <p className="tc-notice" role="status">Loading salary data…</p>;
  if (options.length === 0) return <p className="tc-notice" role="status">Salary data is being refreshed right now. Try again in a few minutes.</p>;

  const chartMax = result ? Math.max(result.total_investment, ...result.trajectory.map((point) => point.cumulative_incremental_earnings), 1) : 1;

  return (
    <div className="trial">
      <form className="tc-form" onSubmit={(event) => { event.preventDefault(); void calculate(); }}>
        <fieldset className="tc-field">
          <legend>Country</legend>
          <div className="tc-chips">
            {countries.map((item) => <button type="button" key={item} className="tc-chip" aria-pressed={country === item} onClick={() => chooseCountry(item)}>{item}</button>)}
          </div>
        </fieldset>
        <label className="tc-field">
          <span>Career you are aiming for <small>{roles.length} with salary data</small></span>
          <select className="tc-input tc-select" value={role} onChange={(event) => { setRole(event.target.value); setResult(null); }}>
            {roles.map((item) => <option key={item.career_target} value={item.career_target}>{item.career_target}</option>)}
          </select>
          {selectedRole && <small className={`tc-hint is-${selectedRole.salary_source}`}>{SOURCE_HINT(selectedRole)}</small>}
        </label>
        <label className="tc-field">
          <span>University <small>optional</small></span>
          <input className="tc-input" value={university} onChange={(event) => setUniversity(event.target.value)} placeholder="e.g. Warsaw University of Technology" maxLength={255} />
        </label>
        <label className="tc-field">
          <span>Study length <b>{studyYears} yrs</b></span>
          <input type="range" min={1} max={6} step={0.5} value={studyYears} onChange={(event) => setStudyYears(Number(event.target.value))} style={{ "--fill": `${((studyYears - 1) / 5) * 100}%` } as React.CSSProperties} />
        </label>
        <label className="tc-field">
          <span>Tuition per year, {currency} <small>0 for a state-funded place</small></span>
          <input className="tc-input" type="number" min={0} step={100} inputMode="numeric" value={tuition} onChange={(event) => setTuition(event.target.value)} aria-invalid={Boolean(fieldError(fieldErrors, "annual_tuition"))} />
          {fieldError(fieldErrors, "annual_tuition") && <em className="tc-error">{fieldError(fieldErrors, "annual_tuition")}</em>}
        </label>
        <label className="tc-field">
          <span>Months to find the first job <b>{search} mo</b></span>
          <input type="range" min={0} max={12} step={1} value={search} onChange={(event) => setSearch(Number(event.target.value))} style={{ "--fill": `${(search / 12) * 100}%` } as React.CSSProperties} />
        </label>
        <fieldset className="tc-field">
          <legend>I want it to pay back within</legend>
          <div className="tc-chips">
            {TARGETS.map((item) => <button type="button" key={item} className="tc-chip" aria-pressed={target === item} onClick={() => setTarget(item)}>{item} years</button>)}
            <button type="button" className="tc-chip" aria-pressed={target === null} onClick={() => setTarget(null)}>No target</button>
          </div>
        </fieldset>
        <button className="tc-submit" type="submit" disabled={busy || !role}>{busy ? "Calculating…" : "Calculate"} <span aria-hidden="true">→</span></button>
        {error && <p className="tc-error" role="alert">{error}</p>}
      </form>

      <section className="tc-result" aria-live="polite" aria-label="Trial result">
        {!result ? (
          <div className="tc-empty">
            <strong>Your result appears here.</strong>
            <p>Fence takes the median starting salary for the career in {country || "your country"}, the pay you would earn without the degree and inflation, then works out the month the degree pays for itself.</p>
          </div>
        ) : (
          <>
            {result.target_payback_years !== null && (
              <p className={`tc-verdict ${result.payback_within_target ? "is-yes" : result.payback_months === null ? "is-never" : "is-no"}`}>
                {result.payback_within_target
                  ? `Pays back within ${result.target_payback_years} years — ${Math.abs(result.payback_target_gap_months ?? 0)} months to spare.`
                  : result.payback_months === null
                    ? `Does not pay back within the 10-year horizon.`
                    : `Pays back ${result.payback_target_gap_months} months later than your ${result.target_payback_years}-year target.`}
              </p>
            )}
            <div className="tc-stats">
              <div className="tc-stat tc-stat--paper"><small>Total investment</small><b>{amount(result.total_investment)} <em>{result.currency}</em></b><span>{money(result.total_direct_cost, result.currency)} direct + {money(result.opportunity_cost, result.currency)} pay given up</span></div>
              <div className="tc-stat tc-stat--lime"><small>Payback after graduating</small><b>{result.payback_months === null ? "10y+" : `${result.payback_months} mo`}</b><span>{result.payback_from_enrollment_months === null ? "not within 10 years" : `${(result.payback_from_enrollment_months / 12).toFixed(1)} years from enrolment`}</span></div>
              <div className="tc-stat tc-stat--violet"><small>10-year ROI</small><b>{result.roi_percent === null ? "—" : `${result.roi_percent >= 0 ? "+" : ""}${result.roi_percent.toFixed(0)}%`}</b><span>start salary {money(result.estimated_start_salary, result.currency)} / yr</span></div>
            </div>

            <div className="tc-chart" role="img" aria-label="Cumulative extra earnings for each year after graduating, against the investment">
              <span className="tc-chart-plot"><span className="tc-chart-line" style={{ bottom: `${(result.total_investment / chartMax) * 100}%` }}><em>investment</em></span></span>
              {result.trajectory.map((point) => (
                <span key={point.year} className={`tc-col ${point.cumulative_incremental_earnings >= result.total_investment ? "is-paid" : ""}`}>
                  <i style={{ height: `${Math.max(0, point.cumulative_incremental_earnings / chartMax) * 100}%` }} />
                  <small>{point.year}</small>
                </span>
              ))}
            </div>

            <div className="tc-scenarios">
              {result.scenarios.map((item) => (
                <div key={item.scenario} className={`tc-scenario tc-scenario--${item.scenario}`}>
                  <small>{SCENARIO_LABEL[item.scenario]}</small>
                  <b>{item.roi_percent === null ? "—" : `${item.roi_percent >= 0 ? "+" : ""}${item.roi_percent.toFixed(0)}%`}</b>
                  <span>{money(item.start_salary, result.currency)} start · {months(item.payback_months)}</span>
                </div>
              ))}
            </div>

            <details className="tc-sources">
              <summary>Where these numbers come from</summary>
              <ul>
                {result.sources.map((source) => (
                  <li key={source.metric}><b>{SOURCE_LABEL[source.metric] ?? source.metric}</b>{source.source_name}{source.sample_size ? ` · ${source.sample_size} vacancies` : ""}{source.confidence ? ` · ${source.confidence} confidence` : ""}</li>
                ))}
                <li><b>Method</b>{result.methodology_version}: today&rsquo;s money, salaries grow with inflation ({result.inflation_percent?.toFixed(2)}%), all work given up while studying, {result.job_search_months} months to the first job.</li>
              </ul>
            </details>

            <div className="tc-next">
              <p>Save it, adjust every assumption and compare universities side by side in your workspace.</p>
              <Link className="tc-submit" href="/register">Save as a scenario <span aria-hidden="true">→</span></Link>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
