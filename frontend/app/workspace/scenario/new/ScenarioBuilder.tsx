"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { AUTH_EXPIRED_EVENT, getCsrfToken, readApiError, type FieldErrors } from "@/lib/api/client";
import { workspaceFetch } from "@/lib/api/workspace";
import UniversitySearch from "./UniversitySearch";
import type {
  CountryEconomicsResponse,
  MarketSnapshotResponse,
  SimulationCreateRequest,
  SimulationProjectionRequest,
  SimulationScenarioResponse,
  TuitionSnapshotResponse,
  TuitionSnapshotSelection,
} from "@/lib/api/generated";

// ─── Types ───────────────────────────────────────────────────────
type SubmitState = "idle" | "checking" | "creating" | "projecting" | "partial" | "error";
type TuitionLookupState = "idle" | "loading" | "found" | "missing" | "error";

type CreatedScenario = SimulationScenarioResponse;
type TuitionSnapshot = TuitionSnapshotResponse;

// Countries with live market, economic and university data; the currency follows the country.
const COUNTRY_CURRENCY: Record<string, string> = { Poland: "PLN", Ukraine: "UAH" };

function fmt(n: number, currency: string) {
  return new Intl.NumberFormat("en", { maximumFractionDigits: 0 }).format(n) + " " + currency;
}

// ─── API error parser ─────────────────────────────────────────────
type FormKey = keyof typeof initialForm;

// Backend field paths (Pydantic loc) -> form inputs, so 422 messages land next to the right field.
const API_FIELD_TO_FORM: Record<string, FormKey> = {
  name: "name",
  "assumptions.university": "university",
  "assumptions.specialization": "specialization",
  "assumptions.country": "country",
  "assumptions.degree": "degree",
  "assumptions.currency": "currency",
  "assumptions.annual_tuition": "annualTuition",
  "assumptions.study_duration_years": "studyDuration",
  "assumptions.career_target": "careerTarget",
  "assumptions.experience_years": "experienceYears",
  annual_start_salary: "annualStartSalary",
  baseline_annual_salary: "baselineAnnualSalary",
  annual_salary_growth_percent: "annualSalaryGrowthPercent",
  baseline_salary_growth_percent: "baselineSalaryGrowthPercent",
  foregone_income_percent: "foregoneIncomePercent",
  mandatory_fees: "mandatoryFees",
  scholarships_and_grants: "scholarshipsAndGrants",
  additional_education_cost: "additionalEducationCost",
  incremental_living_cost: "incrementalLivingCost",
  employment_income_during_study: "employmentIncomeDuringStudy",
  horizon_years: "horizonYears",
  discount_rate_percent: "discountRatePercent",
  inflation_percent: "inflationPercent",
  job_search_months: "jobSearchMonths",
  employment_probability_percent: "employmentProbabilityPercent",
  target_payback_years: "targetPaybackYears",
  "market_snapshot_selection.seniority": "seniority",
};

const DETAILED_FIELDS = new Set<FormKey>([
  "baselineAnnualSalary", "foregoneIncomePercent", "employmentIncomeDuringStudy", "mandatoryFees",
  "scholarshipsAndGrants", "additionalEducationCost", "incrementalLivingCost",
  "annualSalaryGrowthPercent", "baselineSalaryGrowthPercent",
]);

// Which inputs were filled from an official source (they lose that label once edited).
type OfficialInputs = { inflation: boolean; baseline: boolean };

function toFormErrors(errors: FieldErrors): Partial<Record<FormKey, string>> {
  const mapped: Partial<Record<FormKey, string>> = {};
  for (const [path, text] of Object.entries(errors)) {
    // Evidence records reuse the target role and seniority typed in the form.
    const evidence = path.match(/^evidence\.\d+\.(role|seniority|country|currency)$/);
    const key = evidence
      ? ({ role: "careerTarget", seniority: "seniority", country: "country", currency: "currency" } as const)[evidence[1] as "role" | "seniority" | "country" | "currency"]
      : API_FIELD_TO_FORM[path];
    if (key && !mapped[key]) mapped[key] = text;
  }
  return mapped;
}

async function responseError(response: Response): Promise<{ message: string; fields: Partial<Record<FormKey, string>> }> {
  if (response.status === 401 && typeof window !== "undefined") {
    window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
  }
  if (response.status === 401) return { message: "Your secure session has expired. Sign in again before saving this scenario.", fields: {} };
  if (response.status === 403) return { message: "This request could not be verified. Refresh the page and try again.", fields: {} };
  const error = await readApiError(response, "Fence could not complete this request. Review the assumptions and try again.");
  return { message: error.message, fields: toFormErrors(error.fieldErrors) };
}

// ─── Initial form state ───────────────────────────────────────────
const initialForm = {
  name:            "My education decision",
  university:      "",
  specialization:  "",
  country:         "Poland",
  degree:          "Bachelor's degree",
  currency:        "PLN",
  studyDuration:   "3",
  careerTarget:    "",
  experienceYears: "0",
  seniority:       "junior",
  horizonYears:    "10",
  discountRatePercent: "",
  annualTuition:   "",
  studentResidency: "unspecified",
  annualStartSalary: "",
  baselineAnnualSalary: "0",
  annualSalaryGrowthPercent: "0",
  baselineSalaryGrowthPercent: "0",
  foregoneIncomePercent: "100",
  mandatoryFees: "",
  scholarshipsAndGrants: "",
  additionalEducationCost: "",
  incrementalLivingCost: "",
  employmentIncomeDuringStudy: "",
  inflationPercent: "",
  jobSearchMonths: "3",
  employmentProbabilityPercent: "100",
  // Empty: no payback target, the result shows payback without a yes/no verdict.
  targetPaybackYears: "",
};

const PAYBACK_TARGET_PRESETS = ["3", "4", "5", "10"];

const TUITION_IDENTITY_FIELDS = new Set<keyof typeof initialForm>([
  "university",
  "specialization",
  "country",
  "degree",
  "currency",
  "studentResidency",
]);

// ─── Component ───────────────────────────────────────────────────
export default function ScenarioBuilder() {
  const router = useRouter();
  const [form, setForm] = useState(initialForm);
  const [economics, setEconomics] = useState<CountryEconomicsResponse | null>(null);
  const [roles, setRoles] = useState<string[]>([]);
  const [snapshot, setSnapshot] = useState<MarketSnapshotResponse | null>(null);
  const [official, setOfficial] = useState<OfficialInputs>({ inflation: false, baseline: false });
  const [state, setState] = useState<SubmitState>("idle");
  const [message, setMessage] = useState("");
  const [savedScenarioId, setSavedScenarioId] = useState<number | null>(null);
  const [tuitionSnapshot, setTuitionSnapshot] = useState<TuitionSnapshot | null>(null);
  const [tuitionLookupState, setTuitionLookupState] = useState<TuitionLookupState>("idle");
  const [tuitionMessage, setTuitionMessage] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<FormKey, string>>>({});
  const [detailsOpen, setDetailsOpen] = useState(false);
  // A scenario already saved for these exact inputs; a retry then only re-runs the projection.
  const [savedScenario, setSavedScenario] = useState<{ key: string; scenario: CreatedScenario } | null>(null);

  const busy = state === "checking" || state === "creating" || state === "projecting";

  useEffect(() => {
    workspaceFetch<string[]>("/api/market/roles").then(setRoles).catch(() => setRoles([]));
  }, []);

  // Official inflation for the country pre-fills the inflation input (still editable).
  useEffect(() => {
    if (!COUNTRY_CURRENCY[form.country]) { setEconomics(null); return; }
    const controller = new AbortController();
    workspaceFetch<CountryEconomicsResponse>(`/api/market/economics?country=${encodeURIComponent(form.country)}`, { signal: controller.signal })
      .then((data) => {
        setEconomics(data);
        if (data.suggested_inflation_percent != null) {
          setForm((previous) => ({ ...previous, inflationPercent: String(data.suggested_inflation_percent) }));
          setOfficial((previous) => ({ ...previous, inflation: true }));
        }
      })
      .catch(() => setEconomics(null));
    return () => controller.abort();
  }, [form.country]);

  // The market snapshot the calculation would use, shown before submitting.
  useEffect(() => {
    if (!form.careerTarget.trim() || !form.country.trim()) { setSnapshot(null); return; }
    const controller = new AbortController();
    const params = new URLSearchParams({ role: form.careerTarget, country: form.country });
    const timer = window.setTimeout(() => {
      workspaceFetch<MarketSnapshotResponse[]>(`/api/market/snapshots?${params}`, { signal: controller.signal })
        .then((items) => setSnapshot(items.find((item) => item.role.toLowerCase() === form.careerTarget.trim().toLowerCase() && item.currency === form.currency) ?? null))
        .catch(() => setSnapshot(null));
    }, 200);
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, [form.careerTarget, form.country, form.currency]);

  function applyOfficialBaseline() {
    if (economics?.baseline_monthly_wage == null) return;
    update("baselineAnnualSalary", String(Math.round(economics.baseline_monthly_wage * 12 * 100) / 100));
    setOfficial((previous) => ({ ...previous, baseline: true }));
  }

  const estimatedAnnualTuition = Number(form.annualTuition) || 0;
  const estimatedDirectCost = useMemo(
    () => Math.max(
      estimatedAnnualTuition * (Number(form.studyDuration) || 0)
      + (Number(form.mandatoryFees) || 0)
      + (Number(form.additionalEducationCost) || 0)
      + (Number(form.incrementalLivingCost) || 0)
      - (Number(form.scholarshipsAndGrants) || 0),
      0,
    ),
    [estimatedAnnualTuition, form.studyDuration, form.mandatoryFees,
      form.additionalEducationCost, form.incrementalLivingCost, form.scholarshipsAndGrants],
  );

  const estimatedOpportunityCost = useMemo(
    () => Math.max(
      (Number(form.baselineAnnualSalary) || 0)
      * (Number(form.studyDuration) || 0)
      * (Number(form.foregoneIncomePercent) || 0) / 100
      - (Number(form.employmentIncomeDuringStudy) || 0),
      0,
    ),
    [form.baselineAnnualSalary, form.studyDuration, form.foregoneIncomePercent,
      form.employmentIncomeDuringStudy],
  );

  const estimatedTotalCost = estimatedDirectCost + estimatedOpportunityCost;

  const coreFieldsComplete = [form.university, form.specialization, form.careerTarget, form.country, form.annualTuition]
    .filter((v) => v.trim()).length;
  const coreInputsReady = coreFieldsComplete === 5;

  function setPaybackTarget(years: string) {
    update("targetPaybackYears", years);
    // The verdict needs the target inside the horizon, so a longer target extends the horizon.
    const target = Number(years);
    if (Number.isInteger(target) && target >= 1 && target <= 30 && target > Number(form.horizonYears)) {
      update("horizonYears", String(target));
    }
  }

  function update(field: keyof typeof initialForm, value: string) {
    setFieldErrors((previous) => {
      if (!previous[field]) return previous;
      const next = { ...previous };
      delete next[field];
      return next;
    });
    setForm((prev) => {
      const next = field === "currency" || (field === "country" && COUNTRY_CURRENCY[value])
        ? {
          ...prev,
          ...(field === "country" ? { country: value } : {}),
          currency: field === "country" ? COUNTRY_CURRENCY[value] : value,
          annualTuition: "",
          annualStartSalary: "",
          baselineAnnualSalary: "0",
          mandatoryFees: "",
          scholarshipsAndGrants: "",
          additionalEducationCost: "",
          incrementalLivingCost: "",
          employmentIncomeDuringStudy: "",
        }
        : { ...prev, [field]: value };
      if (tuitionSnapshot && TUITION_IDENTITY_FIELDS.has(field)) {
        next.annualTuition = "";
      }
      return next;
    });
    if (field === "inflationPercent") setOfficial((previous) => ({ ...previous, inflation: false }));
    if (field === "baselineAnnualSalary" || field === "currency" || field === "country") setOfficial((previous) => ({ ...previous, baseline: false }));
    if (field === "annualTuition" || TUITION_IDENTITY_FIELDS.has(field)) {
      setTuitionSnapshot(null);
      setTuitionLookupState("idle");
      setTuitionMessage("");
    }
    if (state === "error") setState("idle");
  }

  async function resolveTuitionSnapshot() {
    if (!form.university.trim() || !form.specialization.trim() || !form.country.trim()) {
      setTuitionLookupState("missing");
      setTuitionMessage("Add the university, programme and country before checking verified tuition.");
      return;
    }

    const csrfToken = getCsrfToken();
    if (!csrfToken) {
      setTuitionLookupState("error");
      setTuitionMessage("Refresh the page so Fence can verify this secure request.");
      return;
    }

    setTuitionLookupState("loading");
    setTuitionMessage("");
    try {
      const response = await fetch("/api/tuition/snapshots/resolve", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken,
        },
        body: JSON.stringify({
          university: form.university,
          program: form.specialization,
          country: form.country,
          degree: form.degree,
          student_residency: form.studentResidency as TuitionSnapshotSelection["student_residency"],
          currency: form.currency,
          max_age_days: 1460,
          minimum_confidence: "medium",
          allow_country_fallback: false,
        } satisfies TuitionSnapshotSelection),
      });

      if (!response.ok) {
        setTuitionSnapshot(null);
        setTuitionLookupState(response.status === 422 ? "missing" : "error");
        setTuitionMessage(response.status === 422
          ? "No matching verified record is stored yet. Enter the official fee manually and Fence will label it as user-provided."
          : (await responseError(response)).message);
        return;
      }

      const snapshot = (await response.json()) as TuitionSnapshot;
      setTuitionSnapshot(snapshot);
      setForm((previous) => ({ ...previous, annualTuition: String(snapshot.annual_tuition) }));
      setTuitionLookupState("found");
      setTuitionMessage("Verified stored record selected. Fence will keep its source with this scenario revision.");
    } catch {
      setTuitionSnapshot(null);
      setTuitionLookupState("error");
      setTuitionMessage("Fence could not check stored tuition records. You can still enter the official fee manually.");
    }
  }

  /** Input text -> number for the API. Blank uses the fallback; unparseable text becomes NaN (sent as null) so the API reports the field. */
  function formNumber(value: string, fallback = 0): number {
    const text = value.trim().replace(",", ".");
    return text ? Number(text) : fallback;
  }

  // ─── Submit ───────────────────────────────────────────────────
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setFieldErrors({});
    setState("checking");

    try {
      const csrfToken = getCsrfToken();
      if (!csrfToken) {
        setState("error");
        setMessage("Fence could not verify this browser session. Refresh the page before trying again.");
        return;
      }

      const mutationHeaders = {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      };

      const assumptions: SimulationCreateRequest["assumptions"] = {
        university:           form.university,
        specialization:       form.specialization,
        country:              form.country,
        degree:               form.degree,
        currency:             form.currency,
        study_duration_years: formNumber(form.studyDuration),
        career_target:        form.careerTarget,
        existing_skills:      [],
        additional_education: [],
        courses:              [],
        certifications:       [],
        experience_years:     formNumber(form.experienceYears),
        ...(tuitionSnapshot ? {} : { annual_tuition: estimatedAnnualTuition }),
      };
      const scenarioRequest: SimulationCreateRequest = {
        name: form.name,
        assumptions,
        ...(tuitionSnapshot ? { tuition_snapshot_id: tuitionSnapshot.id } : {}),
      };
      const scenarioKey = JSON.stringify(scenarioRequest);

      let scenario: CreatedScenario;
      if (savedScenario && savedScenario.key === scenarioKey) {
        scenario = savedScenario.scenario;
      } else {
        setState("creating");
        setSavedScenarioId(null);
        const scenarioResponse = await fetch("/api/simulations", {
          method: "POST",
          credentials: "include",
          headers: mutationHeaders,
          body: scenarioKey,
        });

        if (!scenarioResponse.ok) {
          const failure = await responseError(scenarioResponse);
          setFieldErrors(failure.fields);
          setState("error");
          setMessage(failure.message);
          return;
        }

        scenario = (await scenarioResponse.json()) as CreatedScenario;
        setSavedScenario({ key: scenarioKey, scenario });
      }
      setSavedScenarioId(scenario.id);
      setState("projecting");

      const acquiredAt = new Date().toISOString();
      const userEvidence: NonNullable<SimulationProjectionRequest["evidence"]> = [
        ...(!tuitionSnapshot ? [{
          metric: "tuition" as const,
          source_name: "User-provided tuition estimate",
          source_reference: "user-provided:scenario-form",
          acquired_at: acquiredAt,
          country: form.country,
          role: form.careerTarget,
          seniority: form.seniority,
          currency: form.currency,
          confidence: "low" as const,
        }] : []),
        ...(official.inflation && economics && form.inflationPercent.trim() ? [{
          metric: "inflation" as const,
          source_name: `World Bank CPI inflation, median ${economics.inflation_window}`,
          source_reference: economics.series.find((series) => series.indicator === "cpi_inflation")?.source_url || "worldbank:FP.CPI.TOTL.ZG",
          acquired_at: acquiredAt,
          country: form.country,
          role: form.careerTarget,
          seniority: form.seniority,
          currency: form.currency,
          confidence: "high" as const,
        }] : []),
        ...(Number(form.baselineAnnualSalary) > 0 && official.baseline && economics?.baseline_wage_source_url ? [{
          metric: "baseline_salary" as const,
          source_name: economics.baseline_wage_source_name || "Official baseline wage",
          source_reference: economics.baseline_wage_source_url,
          acquired_at: acquiredAt,
          country: form.country,
          role: "Work without this degree",
          seniority: form.seniority,
          currency: form.currency,
          confidence: "high" as const,
        }] : []),
        ...(Number(form.baselineAnnualSalary) > 0 && !(official.baseline && economics?.baseline_wage_source_url) ? [{
          metric: "baseline_salary" as const,
          source_name: "User-provided baseline salary",
          source_reference: "user-provided:scenario-form",
          acquired_at: acquiredAt,
          country: form.country,
          role: "Current employment",
          seniority: form.seniority,
          currency: form.currency,
          confidence: "low" as const,
        }] : []),
        ...(Number(form.employmentIncomeDuringStudy) > 0 ? [{
          metric: "study_income" as const,
          source_name: "User-provided study income estimate",
          source_reference: "user-provided:detailed-analysis",
          acquired_at: acquiredAt,
          country: form.country,
          role: "Employment during study",
          seniority: form.seniority,
          currency: form.currency,
          confidence: "low" as const,
        }] : []),
      ];

      const salarySource: Pick<SimulationProjectionRequest, "annual_start_salary" | "market_snapshot_selection" | "evidence"> = form.annualStartSalary.trim()
        ? {
            annual_start_salary: formNumber(form.annualStartSalary),
            evidence: [
              ...userEvidence,
              {
                metric: "target_start_salary" as const,
                source_name: "User-provided salary estimate",
                source_reference: "user-provided:scenario-form",
                acquired_at: acquiredAt,
                country: form.country,
                role: form.careerTarget,
                seniority: form.seniority,
                currency: form.currency,
                confidence: "low" as const,
              },
            ],
          }
        : {
            market_snapshot_selection: {
              seniority: form.seniority,
              max_age_days: 365,
              minimum_confidence: "medium" as const,
            },
            evidence: userEvidence,
          };

      const projectionResponse = await fetch(
        `/api/simulations/${scenario.id}/revisions/${scenario.current_revision_number}/projections`,
        {
          method: "POST",
          credentials: "include",
          headers: mutationHeaders,
          body: JSON.stringify({
            ...salarySource,
            baseline_annual_salary: formNumber(form.baselineAnnualSalary, 0),
            annual_salary_growth_percent: formNumber(form.annualSalaryGrowthPercent, 0),
            baseline_salary_growth_percent: formNumber(form.baselineSalaryGrowthPercent, 0),
            foregone_income_percent: formNumber(form.foregoneIncomePercent, 100),
            mandatory_fees: formNumber(form.mandatoryFees, 0),
            scholarships_and_grants: formNumber(form.scholarshipsAndGrants, 0),
            additional_education_cost: formNumber(form.additionalEducationCost, 0),
            incremental_living_cost: formNumber(form.incrementalLivingCost, 0),
            employment_income_during_study: form.employmentIncomeDuringStudy.trim() ? formNumber(form.employmentIncomeDuringStudy) : null,
            horizon_years: Number(form.horizonYears),
            // Empty means no NPV; the server never assumes a discount rate.
            discount_rate_percent: form.discountRatePercent.trim() ? formNumber(form.discountRatePercent) : null,
            // Empty inflation keeps the forecast nominal; the result then says so.
            inflation_percent: form.inflationPercent.trim() ? formNumber(form.inflationPercent) : null,
            job_search_months: formNumber(form.jobSearchMonths, 0),
            employment_probability_percent: formNumber(form.employmentProbabilityPercent, 100),
            target_payback_years: form.targetPaybackYears.trim() ? Number(form.targetPaybackYears) : null,
          } satisfies SimulationProjectionRequest),
        },
      );

      if (!projectionResponse.ok) {
        const failure = await responseError(projectionResponse);
        if (projectionResponse.status === 422 && Object.keys(failure.fields).length) {
          // Stay on the form so the user can fix the highlighted inputs; the saved scenario is reused.
          setFieldErrors(failure.fields);
          if (Object.keys(failure.fields).some((key) => DETAILED_FIELDS.has(key as FormKey))) setDetailsOpen(true);
          setState("partial");
          setMessage(`${failure.message} The scenario is saved; fix the fields and submit again to finish the forecast.`);
          return;
        }
        setState("partial");
        setMessage(failure.message);
        router.push(`/workspace/scenarios/${scenario.id}`);
        router.refresh();
        return;
      }

      router.push(`/workspace/scenarios/${scenario.id}`);
      router.refresh();
    } catch {
      setState("error");
      setMessage(
        "Fence could not reach the calculation service. Your browser has not received a confirmed result; check the connection and try again.",
      );
    }
  }

  // ─── Render ───────────────────────────────────────────────────
  return (
    <article className="scenario-workbench">
      <header className="workbench-header">
        <div className="workbench-breadcrumb">
          <span>Workspace</span><i>/</i><strong>ROI Calculator</strong>
        </div>
        <div className="workbench-title-row">
          <div>
            <h1>Build your <span>education forecast</span></h1>
            <p>Estimate the costs, potential returns and payback for your studies.</p>
          </div>
        </div>
      </header>

      <form className="forecast-composer" onSubmit={submit}>

        {/* ── Left: input panel ─────────────────────────────────── */}
        <div className="forecast-input-panel">
          <div className="panel-heading">
            <div>
              <p>Scenario inputs</p>
              <h2>Education details</h2>
              <span>Enter your study information to calculate an estimated return on investment.</span>
            </div>
            <div className="completion-mark">
              <strong>{coreFieldsComplete} / 5</strong>
              <span>core fields</span>
            </div>
          </div>

          {/* Section 01 — Education path */}
          <section className="input-section" aria-labelledby="scenario-education">
            <div className="input-section-title">
              <span>01</span>
              <div><h3 id="scenario-education">Education path</h3><p>What you plan to study and where.</p></div>
            </div>
            <div className="professional-field-grid">
              <Field label="Scenario name" error={fieldErrors.name} className="field-wide">
                <input required minLength={2} maxLength={255} value={form.name}
                  onChange={(e) => update("name", e.target.value)} />
              </Field>
              <Field label="University" error={fieldErrors.university} hint="Live catalogue">
                <UniversitySearch country={form.country} value={form.university} onChange={(value) => update("university", value)} />
              </Field>
              <Field label="Specialization" error={fieldErrors.specialization}>
                <input required minLength={2} value={form.specialization}
                  onChange={(e) => update("specialization", e.target.value)}
                  placeholder="e.g. Computer Science" />
              </Field>
              <Field label="Degree" error={fieldErrors.degree}>
                <select value={form.degree} onChange={(e) => update("degree", e.target.value)}>
                  <option>Bachelor&apos;s degree</option>
                  <option>Master&apos;s degree</option>
                  <option>Postgraduate diploma</option>
                  <option>Professional certificate</option>
                </select>
              </Field>
              <Field label="Duration" error={fieldErrors.studyDuration} hint="Years">
                <input required type="number" min="0.5" max="12" step="0.5"
                  value={form.studyDuration}
                  onChange={(e) => update("studyDuration", e.target.value)} />
              </Field>
              <Field label="Fee category">
                <select value={form.studentResidency}
                  onChange={(e) => update("studentResidency", e.target.value)}>
                  <option value="unspecified">Not specified</option>
                  <option value="domestic">Domestic student</option>
                  <option value="international">International student</option>
                  <option value="eu">EU / EEA student</option>
                  <option value="non_eu">Non-EU student</option>
                  <option value="in_state">US in-state</option>
                  <option value="out_of_state">US out-of-state</option>
                </select>
              </Field>
              <Field label="Annual tuition" error={fieldErrors.annualTuition} hint={tuitionSnapshot ? `Verified · ${form.currency}` : form.currency}>
                <input required type="number" min="0" step="0.01"
                  value={form.annualTuition}
                  readOnly={Boolean(tuitionSnapshot)}
                  onChange={(e) => update("annualTuition", e.target.value)}
                  placeholder="Enter the quoted annual fee" />
              </Field>
              <div className={`tuition-source-panel field-wide is-${tuitionLookupState}`} aria-live="polite">
                <div>
                  <span>Tuition source</span>
                  <strong>{tuitionSnapshot ? "Verified record selected" : "Check Fence data before entering a fee"}</strong>
                  <p>
                    {tuitionSnapshot
                      ? `${tuitionSnapshot.sources[0]?.name || "Stored source"} · ${tuitionSnapshot.academic_year} · ${tuitionSnapshot.confidence} confidence`
                      : "Fence checks stored, validated records only. The calculator never waits for a live provider request."}
                  </p>
                  {tuitionMessage ? <small>{tuitionMessage}</small> : null}
                </div>
                {tuitionSnapshot ? (
                  <button type="button" onClick={() => update("annualTuition", "")}>Use manual fee</button>
                ) : (
                  <button type="button" onClick={resolveTuitionSnapshot}
                    disabled={tuitionLookupState === "loading"}>
                    {tuitionLookupState === "loading" ? "Checking…" : "Check verified tuition"}
                  </button>
                )}
              </div>
            </div>
          </section>

          {/* Section 02 — Career target */}
          <section className="input-section" aria-labelledby="scenario-career">
            <div className="input-section-title">
              <span>02</span>
              <div><h3 id="scenario-career">Career target</h3><p>The role and market your education should unlock.</p></div>
            </div>
            <div className="professional-field-grid">
              <Field label="Target role" error={fieldErrors.careerTarget} className="field-wide" hint="Use the market title">
                <input required minLength={2} value={form.careerTarget} list="market-roles"
                  onChange={(e) => update("careerTarget", e.target.value)}
                  placeholder={roles[0] ? `e.g. ${roles[0]}` : "e.g. Lawyer"} />
                <datalist id="market-roles">{roles.map((role) => <option key={role} value={role} />)}</datalist>
              </Field>
              <Field label="Country" error={fieldErrors.country}>
                <select value={form.country} onChange={(e) => update("country", e.target.value)}>
                  {Object.keys(COUNTRY_CURRENCY).map((country) => <option key={country}>{country}</option>)}
                </select>
              </Field>
              <Field label="Expected seniority" error={fieldErrors.seniority}>
                <select value={form.seniority} onChange={(e) => update("seniority", e.target.value)}>
                  <option value="entry">Entry</option>
                  <option value="junior">Junior</option>
                  <option value="mid">Mid-level</option>
                  <option value="senior">Senior</option>
                </select>
              </Field>
              <Field label="Existing experience" error={fieldErrors.experienceYears} hint="Years">
                <input required type="number" min="0" max="60" step="0.5"
                  value={form.experienceYears}
                  onChange={(e) => update("experienceYears", e.target.value)} />
              </Field>
              <Field label="Currency" error={fieldErrors.currency}>
                <select value={form.currency} onChange={(e) => update("currency", e.target.value)}>
                  <option>PLN</option>
                  <option>UAH</option>
                  <option>EUR</option>
                  <option>USD</option>
                  <option>GBP</option>
                </select>
              </Field>
              <Field label="Expected annual starting salary" error={fieldErrors.annualStartSalary} className="field-wide" hint="Optional manual estimate">
                <input type="number" min="0.01" step="0.01"
                  value={form.annualStartSalary}
                  onChange={(e) => update("annualStartSalary", e.target.value)}
                  placeholder="Leave empty to use a validated market snapshot" />
              </Field>
            </div>
          </section>

          {/* Section 03 — Forecast horizon */}
          <section className="input-section" aria-labelledby="scenario-forecast">
            <div className="input-section-title">
              <span>03</span>
              <div>
                <h3 id="scenario-forecast">Forecast horizon</h3>
                <p>How many years ahead to project your career trajectory.</p>
              </div>
            </div>
            <div className="professional-field-grid">
              <Field label="Forecast horizon" error={fieldErrors.horizonYears} hint="Years">
                <input required type="number" min="1" max="30" step="1"
                  value={form.horizonYears}
                  onChange={(e) => update("horizonYears", e.target.value)} />
              </Field>
              <div className="payback-target-field">
                <span className="payback-target-label">Should pay back within</span>
                <div className="payback-target-options" role="group" aria-label="Target payback period after graduation">
                  <button type="button" className={form.targetPaybackYears === "" ? "is-active" : ""}
                    aria-pressed={form.targetPaybackYears === ""}
                    onClick={() => update("targetPaybackYears", "")}>No target</button>
                  {PAYBACK_TARGET_PRESETS.map((years) => (
                    <button key={years} type="button" className={form.targetPaybackYears === years ? "is-active" : ""}
                      aria-pressed={form.targetPaybackYears === years}
                      onClick={() => setPaybackTarget(years)}>{years} yrs</button>
                  ))}
                  <input type="number" min="1" max="30" step="1" inputMode="numeric" placeholder="N"
                    aria-label="Custom target payback period in years"
                    value={PAYBACK_TARGET_PRESETS.includes(form.targetPaybackYears) ? "" : form.targetPaybackYears}
                    onChange={(e) => setPaybackTarget(e.target.value)} />
                </div>
                <small className={fieldErrors.targetPaybackYears ? "payback-target-hint is-error" : "payback-target-hint"}>
                  {fieldErrors.targetPaybackYears ?? "Years after graduation. The forecast horizon grows to fit the target."}
                </small>
              </div>
              <Field label="Discount rate for NPV" error={fieldErrors.discountRatePercent} hint="Optional, % per year">
                <input type="number" min="0" max="30" step="0.1" inputMode="decimal" placeholder="Leave empty to skip NPV"
                  value={form.discountRatePercent}
                  onChange={(e) => update("discountRatePercent", e.target.value)} />
              </Field>
              <Field label="Inflation" error={fieldErrors.inflationPercent} hint={official.inflation && economics?.inflation_window ? `World Bank median ${economics.inflation_window}` : "% per year · empty = nominal"}>
                <input type="number" min="-10" max="100" step="0.1" inputMode="decimal" placeholder="Leave empty for nominal values"
                  value={form.inflationPercent}
                  onChange={(e) => update("inflationPercent", e.target.value)} />
              </Field>
              <Field label="Job search after graduation" error={fieldErrors.jobSearchMonths} hint="Months without salary">
                <input type="number" min="0" max="24" step="1" value={form.jobSearchMonths}
                  onChange={(e) => update("jobSearchMonths", e.target.value)} />
              </Field>
              <Field label="Chance of a job in this field" error={fieldErrors.employmentProbabilityPercent} hint="% · otherwise baseline pay">
                <input type="number" min="1" max="100" step="1" value={form.employmentProbabilityPercent}
                  onChange={(e) => update("employmentProbabilityPercent", e.target.value)} />
              </Field>
              <div className="field-note-box">
                <span>Calculation policy</span>
                <p>
                  {tuitionSnapshot
                    ? "The selected snapshot is stored with its source and reused deterministically."
                    : "Your explicit tuition is labelled as user-provided. Regional ranges remain orientation only."}
                </p>
              </div>
            </div>
          </section>

          <details className="detailed-analysis" open={detailsOpen} onToggle={(event) => setDetailsOpen(event.currentTarget.open)}>
            <summary>
              <span>Detailed financial analysis</span>
              <small>Optional inputs</small>
            </summary>
            <div className="detailed-analysis-body">
              <p>
                Add only values that apply to your situation. Empty fields are treated as zero;
                employment during study is never assumed automatically.
              </p>
              <div className="professional-field-grid">
                <Field label="Income without this degree" error={fieldErrors.baselineAnnualSalary} hint={official.baseline ? "Official source · per year" : `${form.currency} · per year`}>
                  <input type="number" min="0" step="0.01" value={form.baselineAnnualSalary}
                    onChange={(e) => update("baselineAnnualSalary", e.target.value)} />
                </Field>
                {economics?.baseline_monthly_wage != null && economics.currency === form.currency ? (
                  <div className="field-note-box">
                    <span>{economics.baseline_wage_kind === "minimum_wage" ? "Statutory minimum wage" : "Median vacancy salary"}</span>
                    <p>{fmt(economics.baseline_monthly_wage, form.currency)} per month · {economics.baseline_wage_source_name}</p>
                    <button type="button" className="field-note-action" onClick={applyOfficialBaseline}>Use as baseline</button>
                  </div>
                ) : null}
                <Field label="Income forgone while studying" error={fieldErrors.foregoneIncomePercent} hint="Percent">
                  <input type="number" min="0" max="100" step="1" value={form.foregoneIncomePercent}
                    onChange={(e) => update("foregoneIncomePercent", e.target.value)} />
                </Field>
                <Field label="Total income during study" error={fieldErrors.employmentIncomeDuringStudy} hint={`${form.currency} · optional`}>
                  <input type="number" min="0" step="0.01" value={form.employmentIncomeDuringStudy}
                    onChange={(e) => update("employmentIncomeDuringStudy", e.target.value)}
                    placeholder="Leave empty if not applicable" />
                </Field>
                <Field label="Mandatory fees" error={fieldErrors.mandatoryFees} hint={`${form.currency} · total`}>
                  <input type="number" min="0" step="0.01" value={form.mandatoryFees}
                    onChange={(e) => update("mandatoryFees", e.target.value)} />
                </Field>
                <Field label="Scholarships and grants" error={fieldErrors.scholarshipsAndGrants} hint={form.currency}>
                  <input type="number" min="0" step="0.01" value={form.scholarshipsAndGrants}
                    onChange={(e) => update("scholarshipsAndGrants", e.target.value)} />
                </Field>
                <Field label="Additional education" error={fieldErrors.additionalEducationCost} hint={form.currency}>
                  <input type="number" min="0" step="0.01" value={form.additionalEducationCost}
                    onChange={(e) => update("additionalEducationCost", e.target.value)} />
                </Field>
                <Field label="Incremental living costs" error={fieldErrors.incrementalLivingCost} hint={`${form.currency} · total`}>
                  <input type="number" min="0" step="0.01" value={form.incrementalLivingCost}
                    onChange={(e) => update("incrementalLivingCost", e.target.value)} />
                </Field>
                <Field label="Target salary growth" error={fieldErrors.annualSalaryGrowthPercent} hint="Percent / year">
                  <input type="number" min="0" max="50" step="0.1" value={form.annualSalaryGrowthPercent}
                    onChange={(e) => update("annualSalaryGrowthPercent", e.target.value)} />
                </Field>
                <Field label="Baseline salary growth" error={fieldErrors.baselineSalaryGrowthPercent} hint="Percent / year">
                  <input type="number" min="0" max="50" step="0.1" value={form.baselineSalaryGrowthPercent}
                    onChange={(e) => update("baselineSalaryGrowthPercent", e.target.value)} />
                </Field>
              </div>
            </div>
          </details>
        </div>

        {/* ── Right: forecast preview (sticky) ──────────────────── */}
        <aside className="forecast-preview" aria-label="Scenario preview">

          {/* Header */}
          <div className="forecast-preview-top">
            <div>
              <p>Forecast preview</p>
              <h2>Your education forecast</h2>
              <span>
                {form.university || "University not selected"} · {form.specialization || "Specialization not selected"} — {form.degree}
              </span>
            </div>
            <span className={`forecast-state ${coreInputsReady ? "is-ready" : ""}`}>
              {coreInputsReady ? "Ready to match" : "Unverified input"}
            </span>
          </div>

          {/* Live market range and country economy: stored official data, never typed in */}
          <div className="preview-live-grid">
            <div className="preview-live-card is-lime">
              <span>Market salary · {form.careerTarget || "role"}</span>
              {snapshot ? <>
                <strong>{fmt(snapshot.median_salary, snapshot.currency)}</strong>
                <small>{fmt(snapshot.salary_min, snapshot.currency)} – {fmt(snapshot.salary_max, snapshot.currency)} · {snapshot.sample_size ?? "?"} offers · {snapshot.seniority}</small>
              </> : <>
                <strong>—</strong>
                <small>{roles.length ? `Live data for: ${roles.join(", ")}` : "No market data loaded"}</small>
              </>}
            </div>
            <div className="preview-live-card is-violet">
              <span>{form.country} economy</span>
              {economics?.latest_inflation_percent != null ? <>
                <strong>{economics.latest_inflation_percent}% inflation</strong>
                <small>{economics.latest_inflation_year} · {economics.devaluation_vs_eur_percent != null ? `${economics.currency} vs EUR ${economics.devaluation_vs_eur_percent > 0 ? "+" : ""}${economics.devaluation_vs_eur_percent}% / year` : "no exchange-rate history"}</small>
              </> : <>
                <strong>—</strong>
                <small>Economic data not loaded for this country</small>
              </>}
            </div>
          </div>

          {/* Key metrics */}
          <dl className="forecast-metrics">
            <div>
              <dt>Estimated investment</dt>
              <dd aria-live="polite">{fmt(estimatedTotalCost, form.currency)}</dd>
              <span>
                direct cost + opportunity cost · before taxes
              </span>
            </div>
            <div>
              <dt>Study duration</dt>
              <dd>{form.studyDuration} years</dd>
              <span>{form.degree}</span>
            </div>
            <div>
              <dt>Forecast horizon</dt>
              <dd>{form.horizonYears} years</dd>
              <span>versioned scenario window</span>
            </div>
            <div>
              <dt>Payback target</dt>
              <dd>{form.targetPaybackYears ? `${form.targetPaybackYears} years` : "None"}</dd>
              <span>after graduation</span>
            </div>
          </dl>

          {/* Market evidence callout */}
          <div className="forecast-trust-callout">
            <span aria-hidden="true">!</span>
            <div>
              <strong>{tuitionSnapshot ? "Tuition source verified" : "Evidence required"}</strong>
              <p>
                {tuitionSnapshot
                  ? `Tuition uses snapshot #${tuitionSnapshot.id}. Salary still needs a market snapshot or an explicit estimate.`
                  : "Check stored tuition first. User-provided tuition and salary stay visibly low-confidence."}
              </p>
            </div>
          </div>

          {/* Career & market */}
          <section className="forecast-target" aria-labelledby="preview-target">
            <div className="preview-section-heading">
              <h3 id="preview-target">Career &amp; market match</h3>
              <span>Live inputs</span>
            </div>
            <dl>
              <div><dt>Target role</dt><dd>{form.careerTarget || "Not set"}</dd></div>
              <div><dt>Market</dt><dd>{form.country} · {form.seniority}</dd></div>
              <div><dt>Experience</dt><dd>{form.experienceYears} years</dd></div>
              <div><dt>Tuition source</dt><dd>{tuitionSnapshot ? `${tuitionSnapshot.confidence} confidence` : "User-provided"}</dd></div>
              <div><dt>Salary source</dt><dd>{form.annualStartSalary ? "User-provided estimate" : "Validated snapshot"}</dd></div>
            </dl>
          </section>

          {/* Error / partial feedback */}
          {(state === "error" || state === "partial") && (
            <div className={`professional-feedback ${state === "partial" ? "is-partial" : "is-error"}`} role="alert">
              <strong>{state === "partial" ? "Scenario saved. Forecast paused." : "This scenario was not completed."}</strong>
              <p>{message}</p>
              {state === "partial" && savedScenarioId && (
                <Link href={`/workspace/scenarios/${savedScenarioId}`}>Open saved calculation <span aria-hidden="true">→</span></Link>
              )}
            </div>
          )}

          {/* Submit */}
          <div className="forecast-action">
            <button type="submit" disabled={busy || state === "partial"} aria-busy={busy}>
              {state === "checking"   ? "Checking session…"   :
               state === "creating"  ? "Saving scenario…"    :
               state === "projecting"? "Calculating forecast…": "Calculate forecast"}
              <span aria-hidden="true">→</span>
            </button>
            <p>Deterministic calculation · no AI-generated financial values</p>
          </div>
        </aside>
      </form>
    </article>
  );
}

// ─── Field helper ─────────────────────────────────────────────────
function Field({
  label, hint, error, className = "", children,
}: {
  label: string; hint?: string; error?: string; className?: string; children: React.ReactNode;
}) {
  return (
    <label className={`scenario-field ${error ? "has-error" : ""} ${className}`}>
      <span>{label}{hint && <small>{hint}</small>}</span>
      {children}
      {error && <small className="scenario-field-error" role="alert">{error}</small>}
    </label>
  );
}
