"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { AUTH_EXPIRED_EVENT, getCsrfToken, readApiError, type FieldErrors } from "@/lib/api/client";
import { workspaceFetch, type WorkspaceState } from "@/lib/api/workspace";
import DecimalInput, { parseDecimal } from "../../DecimalInput";
import SearchSelect, { type SearchOption } from "./SearchSelect";
import UniversitySearch from "./UniversitySearch";
import { careersForProgramme, standardStudyYears } from "./programmeRules";
import type {
  CountryEconomicsResponse,
  LivingCostsResponse,
  MarketSnapshotResponse,
  SimulationCreateRequest,
  SimulationProjectionRequest,
  SimulationScenarioResponse,
  SpecializationsResponse,
  StudyProgrammeItem,
} from "@/lib/api/generated";

// ─── Types ───────────────────────────────────────────────────────
type SubmitState = "idle" | "checking" | "projecting" | "error";
type CreatedScenario = SimulationScenarioResponse;
type CostItem = NonNullable<SimulationProjectionRequest["cost_items"]>[number];
type LivingKey = "housing" | "food" | "transport" | "study_materials" | "other_living";

// Countries with live market, economic and university data; the currency follows the country.
const COUNTRY_CURRENCY: Record<string, string> = { Poland: "PLN", Ukraine: "UAH" };
const AVERAGE_STUDY_YEARS = 3.5;
// Every forecast looks ten years past graduation; the person only picks the payback target.
const HORIZON_YEARS = 10;

function fmt(n: number, currency: string) {
  return new Intl.NumberFormat("en", { maximumFractionDigits: 0 }).format(n) + " " + currency;
}

function roundMoney(value: number) {
  return Math.round(value * 100) / 100;
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
  "assumptions.annual_tuition": "annualTuition",
  "assumptions.study_duration_years": "studyDuration",
  "assumptions.career_target": "careerTarget",
  annual_start_salary: "annualStartSalary",
  baseline_annual_salary: "baselineAnnualSalary",
  mandatory_fees: "mandatoryFees",
  scholarships_and_grants: "scholarshipsAndGrants",
  additional_education_cost: "additionalEducationCost",
  employment_income_during_study: "employmentIncomeDuringStudy",
  target_payback_years: "targetPaybackYears",
  "market_snapshot_selection.seniority": "seniority",
};

const DETAILED_FIELDS = new Set<FormKey>([
  "baselineAnnualSalary", "employmentIncomeDuringStudy", "mandatoryFees",
  "scholarshipsAndGrants", "additionalEducationCost", "name",
]);

function toFormErrors(errors: FieldErrors): Partial<Record<FormKey, string>> {
  const mapped: Partial<Record<FormKey, string>> = {};
  for (const [path, text] of Object.entries(errors)) {
    // Evidence records reuse the target role and seniority typed in the form.
    const evidence = path.match(/^evidence\.\d+\.(role|seniority|country)$/);
    const key = evidence
      ? ({ role: "careerTarget", seniority: "seniority", country: "country" } as const)[evidence[1] as "role" | "seniority" | "country"]
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
  if (response.status === 403) {
    // A full plan explains itself; anything else at 403 is a failed browser-session check.
    const error = await readApiError(response, "This request could not be verified. Refresh the page and try again.");
    return { message: /plan/i.test(error.message) ? error.message : "This request could not be verified. Refresh the page and try again.", fields: {} };
  }
  const error = await readApiError(response, "Fence could not complete this request. Review the inputs and try again.");
  return { message: error.message, fields: toFormErrors(error.fieldErrors) };
}

// ─── Initial form state ───────────────────────────────────────────
const initialForm = {
  name:            "",
  country:         "Poland",
  university:      "",
  specialization:  "",
  degree:          "Bachelor's degree",
  // Empty: the 3.5-year average.
  studyDuration:   "",
  annualTuition:   "",
  careerTarget:    "",
  seniority:       "junior",
  annualStartSalary: "",
  // Empty: no payback target, the result shows payback without a yes/no verdict.
  targetPaybackYears: "",
  housing: "",
  food: "",
  transport: "",
  study_materials: "",
  other_living: "",
  mandatoryFees: "",
  additionalEducationCost: "",
  scholarshipsAndGrants: "",
  employmentIncomeDuringStudy: "",
  baselineAnnualSalary: "",
};

const PAYBACK_TARGET_PRESETS = ["3", "5", "7", "10"];
const LEVEL_DEGREE: Record<string, string> = { "first cycle": "Bachelor's degree", "second cycle": "Master's degree", "long-cycle master's": "Master's degree" };
const LEVEL_LABEL: Record<string, string> = { "first cycle": "Bachelor", "second cycle": "Master", "long-cycle master's": "Long-cycle master" };

// ─── Component ───────────────────────────────────────────────────
export default function ScenarioBuilder() {
  const router = useRouter();
  const [form, setForm] = useState(initialForm);
  const [economics, setEconomics] = useState<CountryEconomicsResponse | null>(null);
  const [averages, setAverages] = useState<LivingCostsResponse | null>(null);
  const [universityInfo, setUniversityInfo] = useState<SpecializationsResponse | null>(null);
  const [roles, setRoles] = useState<string[]>([]);
  const [snapshot, setSnapshot] = useState<MarketSnapshotResponse | null>(null);
  // The official document a programme's fee came from; gone once the fee is typed over.
  const [tuitionSource, setTuitionSource] = useState<{ title: string; url: string } | null>(null);
  // The programme level the study length was filled from; gone once the years are typed over.
  const [yearsFromLevel, setYearsFromLevel] = useState<string | null>(null);
  const [state, setState] = useState<SubmitState>("idle");
  const [message, setMessage] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<FormKey, string>>>({});
  const [detailsOpen, setDetailsOpen] = useState(false);
  // A scenario already saved for these exact inputs; a retry then only re-runs the projection.

  // Saved calculations against the plan's limit; the server enforces it, this only says so up front.
  const [slots, setSlots] = useState<{ used: number; limit: number | null; plan: string } | null>(null);
  const planFull = slots?.limit != null && slots.used >= slots.limit;

  const currency = COUNTRY_CURRENCY[form.country];
  const busy = state === "checking" || state === "projecting";

  useEffect(() => {
    workspaceFetch<string[]>("/api/market/roles").then(setRoles).catch(() => setRoles([]));
    workspaceFetch<WorkspaceState>("/api/workspace").then((value) => setSlots({ used: value.user.scenario_count, limit: value.user.scenario_limit ?? null, plan: value.user.plan })).catch(() => setSlots(null));
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const query = `country=${encodeURIComponent(form.country)}`;
    workspaceFetch<CountryEconomicsResponse>(`/api/market/economics?${query}`, { signal: controller.signal })
      .then(setEconomics).catch(() => setEconomics(null));
    workspaceFetch<LivingCostsResponse>(`/api/market/living-costs?${query}`, { signal: controller.signal })
      .then(setAverages).catch(() => setAverages(null));
    return () => controller.abort();
  }, [form.country]);

  // Fee range and address of the chosen university.
  useEffect(() => {
    if (!form.university.trim()) { setUniversityInfo(null); return; }
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      const params = new URLSearchParams({ country: form.country, university: form.university });
      workspaceFetch<SpecializationsResponse>(`/api/workspace/specializations?${params}`, { signal: controller.signal })
        .then(setUniversityInfo).catch(() => setUniversityInfo(null));
    }, 250);
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, [form.country, form.university]);

  // The market snapshot the calculation would use, shown before submitting.
  useEffect(() => {
    if (!form.careerTarget.trim()) { setSnapshot(null); return; }
    const controller = new AbortController();
    const params = new URLSearchParams({ role: form.careerTarget, country: form.country });
    const timer = window.setTimeout(() => {
      workspaceFetch<MarketSnapshotResponse[]>(`/api/market/snapshots?${params}`, { signal: controller.signal })
        .then((items) => setSnapshot(items.find((item) => item.role.toLowerCase() === form.careerTarget.trim().toLowerCase() && item.currency === currency) ?? null))
        .catch(() => setSnapshot(null));
    }, 200);
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, [form.careerTarget, form.country, currency]);

  // A chosen programme narrows the careers to the ones it leads to; without a clue every role is offered.
  const fieldRoles = useMemo(() => careersForProgramme(form.specialization, roles), [form.specialization, roles]);
  const offeredRoles = fieldRoles.length ? fieldRoles : roles;
  const roleOptions = useMemo<SearchOption[]>(() => offeredRoles.map((role) => ({ key: role, label: role })), [offeredRoles]);
  const roleKnown = roles.some((role) => role.toLowerCase() === form.careerTarget.trim().toLowerCase());

  function loadSpecializations(query: string, signal: AbortSignal): Promise<SearchOption<StudyProgrammeItem>[]> {
    const params = new URLSearchParams({ country: form.country, q: query, university: form.university.trim() });
    return workspaceFetch<SpecializationsResponse>(`/api/workspace/specializations?${params}`, { signal }).then((data) =>
      data.items.map((item) => ({
        key: `${item.name}|${item.level ?? ""}|${item.study_mode ?? ""}`,
        label: item.name,
        meta: [item.level ? LEVEL_LABEL[item.level] ?? item.level : null, item.study_mode, item.annual_fee != null ? `${fmt(item.annual_fee, currency)} / year` : null].filter(Boolean).join(" · "),
        data: item,
      })));
  }

  function pickSpecialization(option: SearchOption<StudyProgrammeItem>) {
    const item = option.data;
    const matching = careersForProgramme(option.label, roles);
    // A career from another field (an agronomist for Computer Science) no longer fits.
    const keepRole = (role: string) => !matching.length || !role.trim() || matching.some((fit) => fit.toLowerCase() === role.trim().toLowerCase());
    if (!item) {
      setForm((previous) => ({ ...previous, careerTarget: keepRole(previous.careerTarget) ? previous.careerTarget : "" }));
      return;
    }
    const standardYears = standardStudyYears(item, form.university);
    setForm((previous) => ({
      ...previous,
      careerTarget: keepRole(previous.careerTarget) ? previous.careerTarget : "",
      degree: (item.level && LEVEL_DEGREE[item.level]) || previous.degree,
      // Fee and length come from the programme when known; otherwise the person types them.
      annualTuition: item.annual_fee != null ? String(item.annual_fee) : tuitionSource ? "" : previous.annualTuition,
      studyDuration: standardYears != null ? String(standardYears).replace(".", ",") : yearsFromLevel ? "" : previous.studyDuration,
    }));
    setTuitionSource(item.annual_fee != null && universityInfo?.fee_range
      ? { title: universityInfo.fee_range.source_title, url: universityInfo.fee_range.source_url }
      : null);
    setYearsFromLevel(standardYears != null && item.level ? LEVEL_LABEL[item.level] ?? item.level : null);
  }

  function update(field: FormKey, value: string) {
    setFieldErrors((previous) => {
      if (!previous[field]) return previous;
      const next = { ...previous };
      delete next[field];
      return next;
    });
    setForm((previous) => {
      // Another country means another currency and other institutions: its money fields start empty.
      if (field === "country") return { ...initialForm, country: value, careerTarget: previous.careerTarget, name: previous.name, degree: previous.degree, seniority: previous.seniority, targetPaybackYears: previous.targetPaybackYears };
      // A fee or length read from another university's programme no longer applies.
      if (field === "university") return { ...previous, university: value, annualTuition: tuitionSource ? "" : previous.annualTuition, studyDuration: yearsFromLevel ? "" : previous.studyDuration };
      return { ...previous, [field]: value };
    });
    if (field === "country" || field === "university" || field === "annualTuition") setTuitionSource(null);
    if (field === "country" || field === "university" || field === "studyDuration") setYearsFromLevel(null);
    if (state === "error") setState("idle");
  }

  /** Input text -> number for the API. Blank uses the fallback; unparseable text is sent as null so the API reports the field. */
  function formNumber(value: string, fallback = 0): number {
    const parsed = parseDecimal(value);
    return parsed === null ? fallback : parsed;
  }

  function numberOr(value: string, fallback: number): number {
    const parsed = parseDecimal(value);
    return parsed === null || Number.isNaN(parsed) ? fallback : parsed;
  }

  // ─── Live picture of the costs ────────────────────────────────
  const years = numberOr(form.studyDuration, AVERAGE_STUDY_YEARS) || AVERAGE_STUDY_YEARS;
  const baselineYear = form.baselineAnnualSalary.trim()
    ? numberOr(form.baselineAnnualSalary, 0)
    : (economics?.baseline_monthly_wage ?? 0) * 12;
  const livingLines = (averages?.lines ?? []).map((line) => {
    const typed = form[line.key as LivingKey]?.trim();
    const perMonth = typed ? numberOr(typed, 0) : line.per_month;
    return { key: line.key as LivingKey, label: line.label, average: line.per_month, perMonth, typed: Boolean(typed), total: perMonth * 12 * years };
  });
  const moneyLines = [
    { key: "tuition", label: "Tuition", total: numberOr(form.annualTuition, 0) * years, note: form.annualTuition.trim() ? `${years} years` : "not entered" },
    ...(numberOr(form.mandatoryFees, 0) ? [{ key: "fees", label: "Mandatory fees", total: numberOr(form.mandatoryFees, 0), note: "" }] : []),
    ...livingLines.map((line) => ({ key: line.key, label: line.label, total: line.total, note: `${fmt(line.perMonth, currency)} / mo${line.typed ? "" : " · average"}` })),
    ...(numberOr(form.additionalEducationCost, 0) ? [{ key: "training", label: "Additional training", total: numberOr(form.additionalEducationCost, 0), note: "" }] : []),
    ...(numberOr(form.scholarshipsAndGrants, 0) ? [{ key: "grants", label: "Scholarships and grants", total: -numberOr(form.scholarshipsAndGrants, 0), note: "" }] : []),
    { key: "pay", label: "Pay given up while studying", total: baselineYear * years, note: form.baselineAnnualSalary.trim() ? "your figure" : economics?.baseline_wage_kind === "minimum_wage" ? "minimum wage" : "typical pay" },
    ...(numberOr(form.employmentIncomeDuringStudy, 0) ? [{ key: "income", label: "Income while studying", total: -numberOr(form.employmentIncomeDuringStudy, 0), note: "" }] : []),
  ];
  const estimatedTotalCost = Math.max(moneyLines.reduce((sum, line) => sum + line.total, 0), 0);

  function setPaybackTarget(value: string) {
    update("targetPaybackYears", value);
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

      const university = form.university.trim();
      const specialization = form.specialization.trim();
      const role = form.careerTarget.trim();
      const assumptions: SimulationCreateRequest["assumptions"] = {
        university:           university || null,
        specialization:       specialization || null,
        country:              form.country,
        degree:               form.degree,
        currency,
        study_duration_years: formNumber(form.studyDuration, AVERAGE_STUDY_YEARS),
        career_target:        role,
        existing_skills:      [],
        additional_education: [],
        courses:              [],
        certifications:       [],
        // Not used by the calculation, so the form no longer asks for it.
        experience_years:     0,
        annual_tuition:       formNumber(form.annualTuition),
      };
      const scenarioRequest: SimulationCreateRequest = {
        name: form.name.trim() || [role, specialization || university || form.country].join(" · ").slice(0, 255),
        assumptions,
      };
      setState("projecting");

      const acquiredAt = new Date().toISOString();
      const evidenceBase = { acquired_at: acquiredAt, country: form.country, seniority: form.seniority, currency };
      const userProvided = { source_reference: "user-provided:scenario-form", confidence: "low" as const };
      const evidence: NonNullable<SimulationProjectionRequest["evidence"]> = [
        tuitionSource
          ? { metric: "tuition" as const, source_name: tuitionSource.title, source_reference: tuitionSource.url, confidence: "high" as const, role, ...evidenceBase }
          : { metric: "tuition" as const, source_name: "User-provided tuition estimate", role, ...userProvided, ...evidenceBase },
        ...(form.baselineAnnualSalary.trim() ? [{ metric: "baseline_salary" as const, source_name: "User-provided income without this degree", role: "Current employment", ...userProvided, ...evidenceBase }] : []),
        ...(formNumber(form.employmentIncomeDuringStudy) > 0 ? [{ metric: "study_income" as const, source_name: "User-provided study income estimate", role: "Employment during study", ...userProvided, ...evidenceBase }] : []),
      ];

      const salarySource: Pick<SimulationProjectionRequest, "annual_start_salary" | "market_snapshot_selection" | "evidence"> = form.annualStartSalary.trim()
        ? {
            annual_start_salary: formNumber(form.annualStartSalary),
            evidence: [...evidence, { metric: "target_start_salary" as const, source_name: "User-provided salary estimate", role, ...userProvided, ...evidenceBase }],
          }
        : {
            market_snapshot_selection: { seniority: form.seniority, max_age_days: 365, minimum_confidence: "medium" as const },
            evidence,
          };

      // Only what the person typed; every other line comes from the country average on the server.
      const costItems: CostItem[] = livingLines.filter((line) => line.typed).map((line) => ({
        key: line.key,
        label: line.label,
        per_month: line.perMonth,
        amount: roundMoney(line.total),
        source: "user",
      }));

      // One request: if the forecast fails, the server keeps no empty scenario.
      const response = await fetch("/api/simulations/calculate", {
        method: "POST",
        credentials: "include",
        headers: mutationHeaders,
        body: JSON.stringify({
          scenario: scenarioRequest,
          projection: {
            ...salarySource,
            auto_assumptions: true,
            cost_items: costItems,
            baseline_annual_salary: formNumber(form.baselineAnnualSalary),
            annual_salary_growth_percent: 0,
            baseline_salary_growth_percent: 0,
            foregone_income_percent: 100,
            mandatory_fees: formNumber(form.mandatoryFees),
            scholarships_and_grants: formNumber(form.scholarshipsAndGrants),
            additional_education_cost: formNumber(form.additionalEducationCost),
            incremental_living_cost: 0,
            employment_income_during_study: form.employmentIncomeDuringStudy.trim() ? formNumber(form.employmentIncomeDuringStudy) : null,
            horizon_years: HORIZON_YEARS,
            target_payback_years: form.targetPaybackYears.trim() ? Number(form.targetPaybackYears) : null,
          } satisfies SimulationProjectionRequest,
        }),
      });

      if (!response.ok) {
        const failure = await responseError(response);
        // Stay on the form: everything typed is still there for the next try.
        const noSalaryData = response.status === 422 && !Object.keys(failure.fields).length;
        setFieldErrors(noSalaryData ? { annualStartSalary: failure.message } : failure.fields);
        if (Object.keys(failure.fields).some((key) => DETAILED_FIELDS.has(key as FormKey))) setDetailsOpen(true);
        setState("error");
        setMessage(failure.message);
        return;
      }

      const scenario = (await response.json()) as CreatedScenario;
      router.push(`/workspace/scenarios/${scenario.id}`);
      router.refresh();
    } catch {
      setState("error");
      setMessage("Fence could not reach the calculation service. Your browser has not received a confirmed result; check the connection and try again.");
    }
  }

  const fees = universityInfo?.fee_range;

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
            <p>Tell us the career you want. Fence works out the rest and shows where the money goes.</p>
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
              <span>Only the target role is required. Fill in what you already know.</span>
            </div>
          </div>

          {/* Section 01 — Education path */}
          <section className="input-section" aria-labelledby="scenario-education">
            <div className="input-section-title">
              <span>01</span>
              <div><h3 id="scenario-education">Education path</h3><p>Not decided yet? Leave university and programme empty and add them later.</p></div>
            </div>
            <div className="professional-field-grid">
              <Field label="Country" error={fieldErrors.country} hint={`Amounts in ${currency}`}>
                <select value={form.country} onChange={(e) => update("country", e.target.value)}>
                  {Object.keys(COUNTRY_CURRENCY).map((country) => <option key={country}>{country}</option>)}
                </select>
              </Field>
              <Field label="University" error={fieldErrors.university} hint="Optional">
                <UniversitySearch country={form.country} value={form.university} onChange={(value) => update("university", value)} />
              </Field>
              <Field label="Specialization" error={fieldErrors.specialization} hint="Optional">
                <SearchSelect value={form.specialization} load={loadSpecializations} reloadKey={`${form.country}|${form.university}`}
                  onChange={(value) => update("specialization", value)} onPick={pickSpecialization}
                  placeholder="e.g. Informatyka" loadingText="Searching programmes…" />
              </Field>
              <Field label="Degree" error={fieldErrors.degree}>
                <select value={form.degree} onChange={(e) => update("degree", e.target.value)}>
                  <option>Bachelor&apos;s degree</option>
                  <option>Master&apos;s degree</option>
                  <option>Postgraduate diploma</option>
                  <option>Professional certificate</option>
                </select>
              </Field>
              <Field label="Study years" error={fieldErrors.studyDuration}
                hint={yearsFromLevel ? `Standard length of a ${yearsFromLevel} programme` : `Empty: average ${AVERAGE_STUDY_YEARS}`}>
                <DecimalInput value={form.studyDuration} onChange={(e) => update("studyDuration", e.target.value)} placeholder={`Enter yours, or the average ${String(AVERAGE_STUDY_YEARS).replace(".", ",")} is used`} />
              </Field>
              <Field label="Annual tuition" error={fieldErrors.annualTuition} className="field-wide"
                hint={tuitionSource ? `From the official fee list · ${currency}` : form.specialization.trim() ? `No fee found for this programme: enter it · ${currency}` : `Empty: free · ${currency}`}>
                <DecimalInput value={form.annualTuition} onChange={(e) => update("annualTuition", e.target.value)}
                  placeholder={fees ? `${fmt(fees.min_per_year, fees.currency)} – ${fmt(fees.max_per_year, fees.currency)} at this university` : "The fee per year; leave empty for a free place"} />
              </Field>
              {universityInfo && (fees || universityInfo.address) ? (
                <div className="tuition-source-panel field-wide is-found" aria-live="polite">
                  <div>
                    <span>{form.university}</span>
                    <strong>{fees ? `${fmt(fees.min_per_year, fees.currency)} – ${fmt(fees.max_per_year, fees.currency)} a year` : "Fees not published in our sources"}</strong>
                    <p>
                      {fees ? <>Cheapest to most expensive paid programme, {fees.academic_year}. <a href={fees.source_url} target="_blank" rel="noreferrer">{fees.source_title}</a></> : null}
                      {universityInfo.address ? <> {universityInfo.address}</> : null}
                    </p>
                  </div>
                </div>
              ) : null}
            </div>
          </section>

          {/* Section 02 — Career target */}
          <section className="input-section" aria-labelledby="scenario-career">
            <div className="input-section-title">
              <span>02</span>
              <div><h3 id="scenario-career">Career target</h3><p>The job this education should lead to.</p></div>
            </div>
            <div className="professional-field-grid">
              <Field label="Target role" error={fieldErrors.careerTarget} className="field-wide"
                hint={fieldRoles.length ? `${fieldRoles.length} careers for this programme, or type your own` : `${roles.length || ""} popular roles, or type your own`}>
                <SearchSelect required value={form.careerTarget} options={roleOptions}
                  onChange={(value) => update("careerTarget", value)}
                  placeholder={fieldRoles[0] ? `e.g. ${fieldRoles[0]}` : "e.g. Lawyer"} />
                {form.careerTarget.trim().length >= 2 && !roleKnown && !snapshot
                  ? <small className="field-live-note">Not on our list yet. Fence reads current job listings for this role before showing the calculation.</small>
                  : null}
              </Field>
              <Field label="Expected seniority" error={fieldErrors.seniority}>
                <select value={form.seniority} onChange={(e) => update("seniority", e.target.value)}>
                  <option value="entry">Entry</option>
                  <option value="junior">Junior</option>
                  <option value="mid">Mid-level</option>
                  <option value="senior">Senior</option>
                </select>
              </Field>
              <Field label="Expected annual salary" error={fieldErrors.annualStartSalary} hint={`Optional · ${currency}`}>
                <DecimalInput value={form.annualStartSalary} onChange={(e) => update("annualStartSalary", e.target.value)}
                  placeholder="From the market" />
              </Field>
            </div>
          </section>

          {/* Section 03 — Payback target */}
          <section className="input-section" aria-labelledby="scenario-forecast">
            <div className="input-section-title">
              <span>03</span>
              <div>
                <h3 id="scenario-forecast">Payback target</h3>
                <p>When you want the money back. The forecast always covers {HORIZON_YEARS} years after graduation.</p>
              </div>
            </div>
            <div className="professional-field-grid">
              <div className="payback-target-field field-wide">
                <span className="payback-target-label">Should pay back within</span>
                <div className="payback-target-options" role="group" aria-label="Target payback period after graduation">
                  <button type="button" className={form.targetPaybackYears === "" ? "is-active" : ""}
                    aria-pressed={form.targetPaybackYears === ""}
                    onClick={() => update("targetPaybackYears", "")}>No target</button>
                  {PAYBACK_TARGET_PRESETS.map((value) => (
                    <button key={value} type="button" className={form.targetPaybackYears === value ? "is-active" : ""}
                      aria-pressed={form.targetPaybackYears === value}
                      onClick={() => setPaybackTarget(value)}>{value} yrs</button>
                  ))}
                  <input type="number" min="1" max={HORIZON_YEARS} step="1" inputMode="numeric" placeholder="N"
                    aria-label="Custom target payback period in years"
                    value={PAYBACK_TARGET_PRESETS.includes(form.targetPaybackYears) ? "" : form.targetPaybackYears}
                    onChange={(e) => setPaybackTarget(e.target.value)} />
                </div>
                <small className={fieldErrors.targetPaybackYears ? "payback-target-hint is-error" : "payback-target-hint"}>
                  {fieldErrors.targetPaybackYears ?? `Years after graduation, up to ${HORIZON_YEARS}.`}
                </small>
              </div>
            </div>
          </section>

          <details className="detailed-analysis" open={detailsOpen} onToggle={(event) => setDetailsOpen(event.currentTarget.open)}>
            <summary>
              <span>Detailed financial analysis</span>
              <small>Optional</small>
            </summary>
            <div className="detailed-analysis-body">
              <p>
                Change only what you know. An empty cost per month uses the {form.country} average
                {averages ? <> from <a href={averages.source_url} target="_blank" rel="noreferrer">{averages.source_name}</a></> : null}.
                Enter 0 for anything you will not pay, like housing if you live with your parents.
              </p>
              <div className="professional-field-grid">
                {livingLines.map((line) => (
                  <Field key={line.key} label={line.label} hint={`${currency} / month`}>
                    <DecimalInput value={form[line.key]} onChange={(e) => update(line.key, e.target.value)} placeholder={`Average ${fmt(line.average, currency)}`} />
                  </Field>
                ))}
                <Field label="Additional training and courses" error={fieldErrors.additionalEducationCost} hint={`${currency} · total`}>
                  <DecimalInput value={form.additionalEducationCost} onChange={(e) => update("additionalEducationCost", e.target.value)} placeholder="Courses, licences, certificates" />
                </Field>
                <Field label="Mandatory fees" error={fieldErrors.mandatoryFees} hint={`${currency} · total`}>
                  <DecimalInput value={form.mandatoryFees} onChange={(e) => update("mandatoryFees", e.target.value)} placeholder="Admission, diploma, exams" />
                </Field>
                <Field label="Scholarships and grants" error={fieldErrors.scholarshipsAndGrants} hint={`${currency} · total`}>
                  <DecimalInput value={form.scholarshipsAndGrants} onChange={(e) => update("scholarshipsAndGrants", e.target.value)} />
                </Field>
                <Field label="Income while studying" error={fieldErrors.employmentIncomeDuringStudy} hint={`${currency} · total`}>
                  <DecimalInput value={form.employmentIncomeDuringStudy} onChange={(e) => update("employmentIncomeDuringStudy", e.target.value)} placeholder="A part-time job, if you plan one" />
                </Field>
                <Field label="Income without this degree" error={fieldErrors.baselineAnnualSalary} hint={`${currency} / year`}>
                  <DecimalInput value={form.baselineAnnualSalary} onChange={(e) => update("baselineAnnualSalary", e.target.value)}
                    placeholder={economics?.baseline_monthly_wage != null ? `Empty: ${fmt(economics.baseline_monthly_wage * 12, currency)} (official)` : "What you would earn instead"} />
                </Field>
                <Field label="Calculation name" error={fieldErrors.name} hint="Optional">
                  <input maxLength={255} value={form.name} onChange={(e) => update("name", e.target.value)} placeholder="Named after the role if empty" />
                </Field>
              </div>
            </div>
          </details>
        </div>

        {/* ── Right: forecast preview (sticky) ──────────────────── */}
        <aside className="forecast-preview" aria-label="Scenario preview">

          <div className="forecast-preview-top">
            <div>
              <p>Forecast preview</p>
              <h2>{form.careerTarget.trim() || "Your education forecast"}</h2>
              <span>{[form.university.trim(), form.specialization.trim()].filter(Boolean).join(" · ") || "University and programme not chosen yet"}</span>
            </div>
          </div>

          <div className="preview-live-grid">
            <div className="preview-live-card is-lime">
              <span>Market salary · {form.careerTarget || "role"}</span>
              {snapshot ? <>
                <strong>{fmt(snapshot.median_salary, snapshot.currency)}</strong>
                <small>{fmt(snapshot.salary_min, snapshot.currency)} – {fmt(snapshot.salary_max, snapshot.currency)} · {snapshot.sample_size ?? "?"} offers · {snapshot.seniority}</small>
              </> : <>
                <strong>—</strong>
                <small>{form.careerTarget.trim() ? "Fence collects it when you calculate" : `${roles.length} popular careers in Poland and Ukraine`}</small>
              </>}
            </div>
          </div>

          <dl className="forecast-metrics">
            <div>
              <dt>Estimated investment</dt>
              <dd aria-live="polite">{fmt(estimatedTotalCost, currency)}</dd>
              <span>everything below, before taxes</span>
            </div>
            <div>
              <dt>Study years</dt>
              <dd>{String(years).replace(".", ",")}</dd>
              <span>{form.studyDuration.trim() ? form.degree : "the average, until you enter yours"}</span>
            </div>
          </dl>

          <section className="forecast-target" aria-labelledby="preview-money">
            <div className="preview-section-heading">
              <h3 id="preview-money">Where the money goes</h3>
              <span>You can switch lines off later</span>
            </div>
            <dl className="forecast-cost-lines">
              {moneyLines.map((line) => (
                <div key={line.key}>
                  <dt>{line.label}{line.note ? <small>{line.note}</small> : null}</dt>
                  <dd>{line.total < 0 ? "− " : ""}{fmt(Math.abs(line.total), currency)}</dd>
                </div>
              ))}
            </dl>
          </section>

          {state === "error" && (
            <div className="professional-feedback is-error" role="alert">
              <strong>This calculation was not completed.</strong>
              <p>{message}</p>
            </div>
          )}

          {planFull && slots ? (
            <div className="professional-feedback is-error" role="status">
              <strong>All {slots.limit} calculations on your {slots.plan} plan are used ({slots.used} / {slots.limit}).</strong>
              <p>Delete a saved calculation or <a href="/pricing">upgrade your plan</a> to calculate another.</p>
            </div>
          ) : null}

          <div className="forecast-action">
            <button type="submit" disabled={busy || planFull} aria-busy={busy}>
              {state === "checking"   ? "Checking session…"   :
               state === "projecting"? (snapshot || form.annualStartSalary.trim() ? "Calculating forecast…" : "Reading job listings for this role…") : "Calculate forecast"}
              <span aria-hidden="true">→</span>
            </button>
            <p>All numbers come from the calculation itself, never from AI</p>
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
