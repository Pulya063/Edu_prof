"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";
import { AUTH_EXPIRED_EVENT, getCsrfToken } from "@/lib/api/client";

// ─── Types ───────────────────────────────────────────────────────
type SubmitState = "idle" | "checking" | "creating" | "projecting" | "partial" | "error";
type UniversityType = "public" | "private";
type TuitionLookupState = "idle" | "loading" | "found" | "missing" | "error";

type CreatedScenario = {
  id: number;
  current_revision_number: number;
};

type ApiError = {
  detail?: string | Array<{ msg?: string }>;
};

type TuitionSnapshot = {
  id: number;
  scope: "program" | "university" | "country_average";
  university: string | null;
  program: string | null;
  student_residency: string;
  academic_year: string;
  snapshot_date: string;
  currency: string;
  annual_tuition: string;
  confidence: "low" | "medium" | "high";
  sources: Array<{ name: string; reference: string; url?: string | null }>;
};

// ─── Orientation ranges by currency and university type ───────────
// These ranges are never submitted as financial evidence. The calculation uses
// the user's explicit tuition input or a separately validated data snapshot.
const COST_PRESETS: Record<string, Record<UniversityType, { min: number; max: number; mid: number }>> = {
  PLN: {
    public:  { min: 0,      max: 12_000, mid: 6_000  },
    private: { min: 12_000, max: 30_000, mid: 21_000 },
  },
  EUR: {
    public:  { min: 0,     max: 6_000,  mid: 2_500  },
    private: { min: 5_000, max: 20_000, mid: 12_500 },
  },
  USD: {
    public:  { min: 8_000,  max: 30_000, mid: 19_000 },
    private: { min: 25_000, max: 55_000, mid: 40_000 },
  },
  GBP: {
    public:  { min: 9_250, max: 9_250,  mid: 9_250  },
    private: { min: 12_000, max: 38_000, mid: 25_000 },
  },
};

function getPresetForType(currency: string, type: UniversityType) {
  const map = COST_PRESETS[currency] ?? COST_PRESETS.EUR;
  return map[type];
}

function fmt(n: number, currency: string) {
  return new Intl.NumberFormat("en", { maximumFractionDigits: 0 }).format(n) + " " + currency;
}

// ─── API error parser ─────────────────────────────────────────────
async function responseMessage(response: Response) {
  if (response.status === 401 && typeof window !== "undefined") {
    window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
  }
  try {
    const payload = (await response.json()) as ApiError;
    if (typeof payload.detail === "string") return payload.detail;
    const message = payload.detail?.find((item) => item.msg)?.msg;
    if (message) return message.replace(/^Value error,\s*/i, "");
  } catch { /* ignore */ }
  if (response.status === 401) return "Your secure session has expired. Sign in again before saving this scenario.";
  if (response.status === 403) return "This request could not be verified. Refresh the page and try again.";
  return "Fence could not complete this request. Review the assumptions and try again.";
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
};

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
  const [uniType, setUniType] = useState<UniversityType>("public");
  const [state, setState] = useState<SubmitState>("idle");
  const [message, setMessage] = useState("");
  const [savedScenarioId, setSavedScenarioId] = useState<number | null>(null);
  const [tuitionSnapshot, setTuitionSnapshot] = useState<TuitionSnapshot | null>(null);
  const [tuitionLookupState, setTuitionLookupState] = useState<TuitionLookupState>("idle");
  const [tuitionMessage, setTuitionMessage] = useState("");

  const busy = state === "checking" || state === "creating" || state === "projecting";

  // ── Derived cost values ──────────────────────────────────────
  const preset = useMemo(
    () => getPresetForType(form.currency, uniType),
    [form.currency, uniType],
  );

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

  function update(field: keyof typeof initialForm, value: string) {
    setForm((prev) => {
      const next = field === "currency"
        ? {
          ...prev,
          currency: value,
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
    if (field === "annualTuition" || TUITION_IDENTITY_FIELDS.has(field)) {
      setTuitionSnapshot(null);
      setTuitionLookupState("idle");
      setTuitionMessage("");
    }
    if (state === "error") setState("idle");
  }

  function selectUniversityType(value: UniversityType) {
    if (value === uniType) return;
    setUniType(value);
    if (tuitionSnapshot) {
      setForm((previous) => ({ ...previous, annualTuition: "" }));
    }
    setTuitionSnapshot(null);
    setTuitionLookupState("idle");
    setTuitionMessage("");
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
          student_residency: form.studentResidency,
          institution_type: uniType,
          currency: form.currency,
          max_age_days: 1460,
          minimum_confidence: "medium",
          allow_country_fallback: false,
        }),
      });

      if (!response.ok) {
        setTuitionSnapshot(null);
        setTuitionLookupState(response.status === 422 ? "missing" : "error");
        setTuitionMessage(response.status === 422
          ? "No matching verified record is stored yet. Enter the official fee manually and Fence will label it as user-provided."
          : await responseMessage(response));
        return;
      }

      const snapshot = (await response.json()) as TuitionSnapshot;
      setTuitionSnapshot(snapshot);
      setForm((previous) => ({ ...previous, annualTuition: snapshot.annual_tuition }));
      setTuitionLookupState("found");
      setTuitionMessage("Verified stored record selected. Fence will keep its source with this scenario revision.");
    } catch {
      setTuitionSnapshot(null);
      setTuitionLookupState("error");
      setTuitionMessage("Fence could not check stored tuition records. You can still enter the official fee manually.");
    }
  }

  // ─── Submit ───────────────────────────────────────────────────
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setSavedScenarioId(null);
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

      setState("creating");
      const assumptions = {
        university:           form.university,
        specialization:       form.specialization,
        country:              form.country,
        degree:               form.degree,
        currency:             form.currency,
        study_duration_years: form.studyDuration,
        career_target:        form.careerTarget,
        existing_skills:      [],
        additional_education: [],
        courses:              [],
        certifications:       [],
        experience_years:     form.experienceYears,
        ...(tuitionSnapshot ? {} : { annual_tuition: String(estimatedAnnualTuition) }),
      };
      const scenarioResponse = await fetch("/api/simulations", {
        method: "POST",
        credentials: "include",
        headers: mutationHeaders,
        body: JSON.stringify({
          name: form.name,
          assumptions,
          ...(tuitionSnapshot ? { tuition_snapshot_id: tuitionSnapshot.id } : {}),
        }),
      });

      if (!scenarioResponse.ok) {
        setState("error");
        setMessage(await responseMessage(scenarioResponse));
        return;
      }

      const scenario = (await scenarioResponse.json()) as CreatedScenario;
      setSavedScenarioId(scenario.id);
      setState("projecting");

      const acquiredAt = new Date().toISOString();
      const userEvidence = [
        ...(!tuitionSnapshot ? [{
          metric: "tuition",
          source_name: "User-provided tuition estimate",
          source_reference: "user-provided:scenario-form",
          acquired_at: acquiredAt,
          country: form.country,
          role: form.careerTarget,
          seniority: form.seniority,
          currency: form.currency,
          confidence: "low",
        }] : []),
        ...(Number(form.baselineAnnualSalary) > 0 ? [{
          metric: "baseline_salary",
          source_name: "User-provided baseline salary",
          source_reference: "user-provided:scenario-form",
          acquired_at: acquiredAt,
          country: form.country,
          role: "Current employment",
          seniority: form.seniority,
          currency: form.currency,
          confidence: "low",
        }] : []),
        ...(Number(form.employmentIncomeDuringStudy) > 0 ? [{
          metric: "study_income",
          source_name: "User-provided study income estimate",
          source_reference: "user-provided:detailed-analysis",
          acquired_at: acquiredAt,
          country: form.country,
          role: "Employment during study",
          seniority: form.seniority,
          currency: form.currency,
          confidence: "low",
        }] : []),
      ];

      const salarySource = form.annualStartSalary.trim()
        ? {
            annual_start_salary: form.annualStartSalary,
            evidence: [
              ...userEvidence,
              {
                metric: "target_start_salary",
                source_name: "User-provided salary estimate",
                source_reference: "user-provided:scenario-form",
                acquired_at: acquiredAt,
                country: form.country,
                role: form.careerTarget,
                seniority: form.seniority,
                currency: form.currency,
                confidence: "low",
              },
            ],
          }
        : {
            market_snapshot_selection: {
              seniority: form.seniority,
              max_age_days: 365,
              minimum_confidence: "medium",
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
            baseline_annual_salary: form.baselineAnnualSalary || "0",
            annual_salary_growth_percent: form.annualSalaryGrowthPercent || "0",
            baseline_salary_growth_percent: form.baselineSalaryGrowthPercent || "0",
            foregone_income_percent: form.foregoneIncomePercent || "100",
            mandatory_fees: form.mandatoryFees || "0",
            scholarships_and_grants: form.scholarshipsAndGrants || "0",
            additional_education_cost: form.additionalEducationCost || "0",
            incremental_living_cost: form.incrementalLivingCost || "0",
            employment_income_during_study: form.employmentIncomeDuringStudy || null,
            horizon_years: Number(form.horizonYears),
          }),
        },
      );

      if (!projectionResponse.ok) {
        setState("partial");
        setMessage(await responseMessage(projectionResponse));
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
              <Field label="Scenario name" className="field-wide">
                <input required minLength={2} maxLength={255} value={form.name}
                  onChange={(e) => update("name", e.target.value)} />
              </Field>
              <Field label="University">
                <input required minLength={2} value={form.university}
                  onChange={(e) => update("university", e.target.value)}
                  placeholder="e.g. University of Warsaw" />
              </Field>
              <Field label="Specialization">
                <input required minLength={2} value={form.specialization}
                  onChange={(e) => update("specialization", e.target.value)}
                  placeholder="e.g. Computer Science" />
              </Field>
              <Field label="Degree">
                <select value={form.degree} onChange={(e) => update("degree", e.target.value)}>
                  <option>Bachelor&apos;s degree</option>
                  <option>Master&apos;s degree</option>
                  <option>Postgraduate diploma</option>
                  <option>Professional certificate</option>
                </select>
              </Field>
              <Field label="Duration" hint="Years">
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
              <Field label="Annual tuition" hint={tuitionSnapshot ? `Verified · ${form.currency}` : form.currency}>
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
              <Field label="Target role" className="field-wide" hint="Use the market title">
                <input required minLength={2} value={form.careerTarget}
                  onChange={(e) => update("careerTarget", e.target.value)}
                  placeholder="e.g. Software Engineer" />
              </Field>
              <Field label="Country">
                <input required minLength={2} value={form.country}
                  onChange={(e) => update("country", e.target.value)} />
              </Field>
              <Field label="Expected seniority">
                <select value={form.seniority} onChange={(e) => update("seniority", e.target.value)}>
                  <option value="entry">Entry</option>
                  <option value="junior">Junior</option>
                  <option value="mid">Mid-level</option>
                  <option value="senior">Senior</option>
                </select>
              </Field>
              <Field label="Existing experience" hint="Years">
                <input required type="number" min="0" max="60" step="0.5"
                  value={form.experienceYears}
                  onChange={(e) => update("experienceYears", e.target.value)} />
              </Field>
              <Field label="Currency">
                <select value={form.currency} onChange={(e) => update("currency", e.target.value)}>
                  <option>PLN</option>
                  <option>EUR</option>
                  <option>USD</option>
                  <option>GBP</option>
                </select>
              </Field>
              <Field label="Expected annual starting salary" className="field-wide" hint="Optional manual estimate">
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
              <Field label="Forecast horizon" hint="Years">
                <input required type="number" min="1" max="30" step="1"
                  value={form.horizonYears}
                  onChange={(e) => update("horizonYears", e.target.value)} />
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

          <details className="detailed-analysis">
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
                <Field label="Current annual salary" hint={form.currency}>
                  <input type="number" min="0" step="0.01" value={form.baselineAnnualSalary}
                    onChange={(e) => update("baselineAnnualSalary", e.target.value)} />
                </Field>
                <Field label="Income forgone while studying" hint="Percent">
                  <input type="number" min="0" max="100" step="1" value={form.foregoneIncomePercent}
                    onChange={(e) => update("foregoneIncomePercent", e.target.value)} />
                </Field>
                <Field label="Total income during study" hint={`${form.currency} · optional`}>
                  <input type="number" min="0" step="0.01" value={form.employmentIncomeDuringStudy}
                    onChange={(e) => update("employmentIncomeDuringStudy", e.target.value)}
                    placeholder="Leave empty if not applicable" />
                </Field>
                <Field label="Mandatory fees" hint={`${form.currency} · total`}>
                  <input type="number" min="0" step="0.01" value={form.mandatoryFees}
                    onChange={(e) => update("mandatoryFees", e.target.value)} />
                </Field>
                <Field label="Scholarships and grants" hint={form.currency}>
                  <input type="number" min="0" step="0.01" value={form.scholarshipsAndGrants}
                    onChange={(e) => update("scholarshipsAndGrants", e.target.value)} />
                </Field>
                <Field label="Additional education" hint={form.currency}>
                  <input type="number" min="0" step="0.01" value={form.additionalEducationCost}
                    onChange={(e) => update("additionalEducationCost", e.target.value)} />
                </Field>
                <Field label="Incremental living costs" hint={`${form.currency} · total`}>
                  <input type="number" min="0" step="0.01" value={form.incrementalLivingCost}
                    onChange={(e) => update("incrementalLivingCost", e.target.value)} />
                </Field>
                <Field label="Target salary growth" hint="Percent / year">
                  <input type="number" min="0" max="50" step="0.1" value={form.annualSalaryGrowthPercent}
                    onChange={(e) => update("annualSalaryGrowthPercent", e.target.value)} />
                </Field>
                <Field label="Baseline salary growth" hint="Percent / year">
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

          {/* ── Public / Private toggle ──────────────────────────── */}
          <div className="uni-type-toggle" role="group" aria-label="University type">
            <button
              type="button"
              className={`uni-type-btn ${uniType === "public" ? "is-active" : ""}`}
              onClick={() => selectUniversityType("public")}
            >
              <svg viewBox="0 0 20 20" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10 2 2 7h16L10 2ZM4 7v8M8 7v8M12 7v8M16 7v8M2 15h16" />
              </svg>
              Public university
            </button>
            <button
              type="button"
              className={`uni-type-btn ${uniType === "private" ? "is-active" : ""}`}
              onClick={() => selectUniversityType("private")}
            >
              <svg viewBox="0 0 20 20" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                <rect x="2" y="9" width="16" height="9" rx="1.5" />
                <path d="M6 9V6a4 4 0 0 1 8 0v3" />
              </svg>
              Private university
            </button>
          </div>

          {/* Regional orientation, never a submitted calculation input */}
          <div className="cost-estimate-row">
            <div className="cost-estimate-item">
              <span>Regional orientation range</span>
              <strong aria-live="polite">
                {fmt(preset.min, form.currency)} – {fmt(preset.max, form.currency)}
              </strong>
              <small>
                {uniType === "public"
                  ? "Public-university orientation · not used automatically"
                  : "Private-university orientation · not used automatically"}
              </small>
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

          {/* Cost comparison note */}
          <section className="forecast-assumptions" aria-labelledby="preview-assumptions">
            <div className="preview-section-heading">
              <h3 id="preview-assumptions">Cost comparison</h3>
              <span>Toggle to compare</span>
            </div>
            <div className="assumption-row">
              <span>Public (mid)</span>
              <i><b style={{ width: `${Math.min((getPresetForType(form.currency, "public").mid / getPresetForType(form.currency, "private").max) * 100, 100)}%` }} /></i>
              <strong>{fmt(getPresetForType(form.currency, "public").mid, form.currency)}</strong>
            </div>
            <div className="assumption-row">
              <span>Private (mid)</span>
              <i><b className="is-violet" style={{ width: "100%" }} /></i>
              <strong>{fmt(getPresetForType(form.currency, "private").mid, form.currency)}</strong>
            </div>
            <p className="cost-data-note">
              Regional ranges are orientation only. Exact stored fees are used only after an explicit source match.
            </p>
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
  label, hint, className = "", children,
}: {
  label: string; hint?: string; className?: string; children: React.ReactNode;
}) {
  return (
    <label className={`scenario-field ${className}`}>
      <span>{label}{hint && <small>{hint}</small>}</span>
      {children}
    </label>
  );
}
