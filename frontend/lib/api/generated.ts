// AUTO-GENERATED from app/schemas.py by app/scripts/generate_ts_types.py. Do not edit by hand.
// Regenerate: uv run --no-sync python -m app.scripts.generate_ts_types

/** ISO-8601 date-time string. */
export type IsoDateTime = string;
/** ISO-8601 calendar date (YYYY-MM-DD). */
export type IsoDate = string;


// ---- Responses ----

export type AuthMeResponse = {
  id: number;
  email: string;
  username: string;
  created_at: IsoDateTime;
  plan: string;
  plan_limits: AuthPlanLimits;
  plan_features: string[];
  usage: AuthUsage;
  calculations_remaining: number | null;
  is_admin: boolean;
};

export type AuthPlanLimits = {
  roi_calculations: number | null;
  roadmaps: number | null;
};

export type AuthProviderStatus = {
  configured: boolean;
};

export type AuthProvidersResponse = {
  google: AuthProviderStatus;
};

export type AuthUsage = {
  roi_calculations: number;
  roadmaps: number;
};

export type CheckoutResponse = {
  checkout_url: string;
  session_id: string;
};

/** Official macro data and the deterministic defaults derived from it. */
export type CountryEconomicsResponse = {
  country: string;
  currency: string | null;
  latest_inflation_percent: number | null;
  latest_inflation_year: number | null;
  suggested_inflation_percent: number | null;
  inflation_window: string | null;
  devaluation_vs_eur_percent: number | null;
  baseline_monthly_wage: number | null;
  baseline_wage_kind: "minimum_wage" | "median_vacancy_wage" | null;
  baseline_wage_period: IsoDate | null;
  baseline_wage_source_name: string | null;
  baseline_wage_source_url: string | null;
  graduate_unemployment_percent: number | null;
  graduate_unemployment_year: number | null;
  series: EconomicSeries[];
};

export type EconomicPoint = {
  period: IsoDate;
  value: number;
};

export type EconomicSeries = {
  indicator: string;
  unit: string;
  source_name: string;
  source_url: string;
  acquired_at: IsoDateTime;
  points: EconomicPoint[];
};

export type LivingCostLine = {
  key: string;
  label: string;
  per_month: number;
};

export type LivingCostsResponse = {
  country: string;
  currency: string;
  source_name: string;
  source_url: string;
  lines: LivingCostLine[];
};

export type MarketNewsItem = {
  title: string;
  url: string;
  published_at: IsoDateTime | null;
  source: string | null;
};

export type MarketNewsResponse = {
  query: string;
  feed_url: string;
  items: MarketNewsItem[];
};

export type MarketSnapshotResponse = {
  id: number;
  role: string;
  country: string;
  seniority: string;
  snapshot_date: IsoDate;
  currency: string;
  salary_basis: string;
  salary_min: number;
  median_salary: number;
  salary_max: number;
  vacancy_count: number | null;
  demand_index: number | null;
  sources: MarketSnapshotSource[];
  acquired_at: IsoDateTime;
  sample_size: number | null;
  confidence: string;
  methodology_version: string;
  validation_status: string;
  fingerprint: string;
  created_at: IsoDateTime;
};

export type MarketSnapshotSource = {
  name: string;
  reference: string;
  url: string | null;
  acquired_at: IsoDateTime;
};

export type PaymentPlanOption = {
  plan: "pro" | "business" | "enterprise";
  plan_name: string;
  cycle: "monthly" | "yearly";
  amount: number;
  currency: string;
  available: boolean;
};

export type PaymentPlansResponse = {
  configured: boolean;
  publishable_key: string | null;
  current_plan: string | null;
  options: PaymentPlanOption[];
};

export type PaymentStatusResponse = {
  session_id: string;
  plan: "pro" | "business" | "enterprise";
  plan_name: string;
  billing_cycle: "monthly" | "yearly";
  status: "pending" | "paid" | "failed" | "expired" | "canceled";
  amount_expected: number;
  amount_total: number | null;
  currency: string;
  paid_at: IsoDateTime | null;
  created_at: IsoDateTime;
  current_plan: string;
};

/** Advisory AI review stored separately from canonical financial numbers. */
export type ProjectionAIReviewResponse = {
  status: "pending" | "running" | "completed" | "failed" | "not_configured";
  provider_model: string | null;
  confidence_score: number | null;
  ai_risk_score: number | null;
  calculation_consistent: boolean | null;
  prediction_summary: string | null;
  verdict: string | null;
  recommendations: string[];
  risks: string[];
  suggested_adjustments: Record<string, unknown>[];
  error_message: string | null;
  completed_at: IsoDateTime | null;
};

export type ProjectionCalculationInputs = {
  cost_items: ProjectionCostItem[];
  market_snapshot_id: number | null;
  annual_start_salary: number | null;
  baseline_annual_salary: number | null;
  annual_salary_growth_percent: number | null;
  baseline_salary_growth_percent: number | null;
  foregone_income_percent: number | null;
  mandatory_fees: number | null;
  scholarships_and_grants: number | null;
  additional_education_cost: number | null;
  incremental_living_cost: number | null;
  employment_income_during_study: number | null;
  horizon_years: number | null;
  discount_rate_percent: number | null;
  inflation_percent: number | null;
  job_search_months: number | null;
  employment_probability_percent: number | null;
  target_payback_years: number | null;
};

/** Detailed v2 breakdown; fields stay optional for readable v1 history. */
export type ProjectionCostBreakdown = {
  tuition: number | null;
  mandatory_fees: number | null;
  additional_education: number | null;
  incremental_living_cost: number | null;
  scholarships_and_grants: number | null;
  gross_direct_cost: number | null;
  net_direct_cost: number | null;
  baseline_income_during_study: number | null;
  employment_income_during_study: number | null;
  opportunity_cost: number | null;
};

/** One visible line of the investment. Switched off, it counts as nothing. */
export type ProjectionCostItem = {
  key: "tuition" | "mandatory_fees" | "housing" | "food" | "transport" | "study_materials" | "other_living" | "additional_training" | "scholarships" | "pay_given_up" | "income_during_study";
  label: string;
  amount: number;
  per_month: number | null;
  enabled: boolean;
  editable: boolean;
  source: "user" | "country_average" | "calculated" | "stored" | "ai";
  source_name: string | null;
  source_url: string | null;
};

/** Походження конкретного показника; валідна форма не підтверджує правдивість джерела. */
export type ProjectionEvidence = {
  metric: "target_start_salary" | "baseline_salary" | "salary_growth" | "tuition" | "mandatory_fees" | "scholarships" | "study_income" | "inflation" | "career_level";
  source_name: string;
  source_reference: string;
  acquired_at: IsoDateTime;
  country: string;
  role: string;
  seniority: string;
  currency: string;
  sample_size: number | null;
  confidence: "low" | "medium" | "high";
};

/** What a change to the cost lines would do. Calculated by the engine, not stored. */
export type ProjectionPreviewResponse = {
  total_direct_cost: number;
  opportunity_cost: number;
  total_investment: number;
  estimated_start_salary: number;
  cost_breakdown: ProjectionCostBreakdown;
  payback_months: number | null;
  payback_from_enrollment_months: number | null;
  break_even_reached: boolean;
  target_payback_years: number | null;
  payback_within_target: boolean | null;
  payback_target_gap_months: number | null;
  horizon_years: number;
  cumulative_incremental_earnings: number;
  roi_percent: number | null;
  npv: number | null;
  scenario_outcomes: ProjectionScenarioOutcome[];
  salary_trajectory: SalaryTrajectoryPoint[];
  cost_items: ProjectionCostItem[];
};

/** Lines switched or edited on the full calculation; save stores them as a new projection. */
export type ProjectionRecalculateRequest = {
  cost_items: ProjectionCostItem[];
  save: boolean;
};

/** v3: one start-salary scenario on the same costs, growth and baseline. */
export type ProjectionScenarioOutcome = {
  scenario: "pessimistic" | "base" | "optimistic";
  start_salary: number;
  cumulative_incremental_earnings: number;
  roi_percent: number | null;
  payback_months: number | null;
  break_even_reached: boolean;
  npv: number | null;
};

export type ProjectionSnapshotProvenance = {
  snapshot: MarketSnapshotResponse;
  age_days: number;
  selected_metric: "median_salary";
  selected_value: number;
};

/** Рядок дашборду: сценарій і підсумок його останнього прогнозу поточної ревізії, якщо він є. */
export type RecentCalculationSummary = {
  scenario_id: number;
  name: string;
  status: string;
  target_role: string;
  country: string;
  currency: string;
  revision_number: number;
  updated_at: IsoDateTime;
  projection_id: number | null;
  methodology_version: string | null;
  total_investment: number | null;
  roi_percent: number | null;
  payback_months: number | null;
  break_even_reached: boolean | null;
  horizon_years: number | null;
};

/** Рік після навчання: дохід цільового шляху мінус альтернативний дохід. */
export type SalaryTrajectoryPoint = {
  year: number;
  target_salary: number;
  baseline_salary: number;
  incremental_earnings: number;
  cumulative_incremental_earnings: number;
};

/** Вхідні умови освіти й кар'єри; після вибору tuition зберігаються в ревізії. */
export type SimulationAssumptions = {
  university: string | null;
  specialization: string | null;
  country: string;
  degree: string;
  currency: string;
  annual_tuition: number | null;
  study_duration_years: number;
  career_target: string;
  existing_skills: string[];
  additional_education: string[];
  courses: string[];
  certifications: string[];
  experience_years: number;
};

/** Стан звіту: сценаріїв немає, є лише умови або вже є фінансовий прогноз. */
export type SimulationOverviewResponse = {
  status: "empty" | "scenario_only" | "projected";
  scenario: SimulationScenarioResponse | null;
  projection: SimulationProjectionResponse | null;
  explainability: SimulationProjectionExplainabilityResponse | null;
  recent_calculations: RecentCalculationSummary[];
};

/** Джерела зарплати й обмеження збереженого прогнозу без нового розрахунку. */
export type SimulationProjectionExplainabilityResponse = {
  projection_id: number;
  calculation_type: "deterministic";
  ai_generated: false;
  methodology_version: string;
  salary_basis: string;
  currency: string;
  salary_source_kind: "market_snapshot" | "manual_evidence";
  selected_salary_metric: "median_salary" | "annual_start_salary";
  estimated_start_salary: number;
  source_snapshots: ProjectionSnapshotProvenance[];
  source_integrity: "complete" | "missing";
  missing_source_snapshot_refs: string[];
  evidence: ProjectionEvidence[];
  unverified_assumptions: string[];
};

/** Збережений deterministic результат із методологією, входами й обмеженнями. */
export type SimulationProjectionResponse = {
  id: number;
  revision_id: number;
  methodology_version: string;
  input_fingerprint: string;
  currency: string;
  salary_basis: string;
  total_direct_cost: number;
  opportunity_cost: number;
  total_investment: number;
  estimated_start_salary: number;
  calculation_inputs: ProjectionCalculationInputs;
  cost_breakdown: ProjectionCostBreakdown;
  payback_months: number | null;
  payback_from_enrollment_months: number | null;
  break_even_reached: boolean;
  target_payback_years: number | null;
  payback_within_target: boolean | null;
  payback_target_gap_months: number | null;
  horizon_years: number;
  cumulative_incremental_earnings: number;
  roi_percent: number | null;
  npv: number | null;
  scenario_outcomes: ProjectionScenarioOutcome[];
  salary_trajectory: SalaryTrajectoryPoint[];
  evidence: ProjectionEvidence[];
  source_snapshot_refs: string[];
  unverified_assumptions: string[];
  ai_review: ProjectionAIReviewResponse | null;
  created_at: IsoDateTime;
};

/** Збережені умови й посилання на джерела для відтворення рішення. */
export type SimulationRevisionResponse = {
  id: number;
  revision_number: number;
  assumptions: SimulationAssumptions;
  methodology_version: string;
  source_snapshot_refs: string[];
  change_note: string | null;
  created_at: IsoDateTime;
};

/** Рядок списку: умови поточної ревізії та числа останнього прогнозу; без прогнозу числа порожні. */
export type SimulationScenarioListItem = {
  id: number;
  name: string;
  status: string;
  current_revision_number: number;
  target_role: string;
  country: string;
  currency: string;
  created_at: IsoDateTime;
  updated_at: IsoDateTime;
  university: string | null;
  specialization: string | null;
  degree: string | null;
  study_duration_years: number | null;
  annual_tuition: number | null;
  projection_id: number | null;
  total_investment: number | null;
  roi_percent: number | null;
  payback_months: number | null;
};

/** Сценарій разом з історією його умов, а не лише поточними значеннями. */
export type SimulationScenarioResponse = {
  id: number;
  name: string;
  status: string;
  current_revision_number: number;
  target_role: string;
  country: string;
  currency: string;
  created_at: IsoDateTime;
  updated_at: IsoDateTime;
  revisions: SimulationRevisionResponse[];
};

/** Короткий запис для списків; фінансові результати читаються окремо. */
export type SimulationScenarioSummary = {
  id: number;
  name: string;
  status: string;
  current_revision_number: number;
  target_role: string;
  country: string;
  currency: string;
  created_at: IsoDateTime;
  updated_at: IsoDateTime;
};

export type SpecializationsResponse = {
  items: StudyProgrammeItem[];
  fee_range: StudyFeeRange | null;
  address: string | null;
};

export type StudyFeeRange = {
  min_per_year: number;
  max_per_year: number;
  currency: string;
  academic_year: string;
  source_title: string;
  source_url: string;
};

export type StudyProgrammeItem = {
  name: string;
  level: string | null;
  annual_fee: number | null;
  study_mode: string | null;
};

export type TrialProjectionOption = {
  country: string;
  currency: string;
  career_target: string;
  median_salary: number;
  seniority: string;
  salary_source: "listings" | "official";
};

export type TrialProjectionResponse = {
  preview: "trial";
  methodology_version: string;
  country: string;
  career_target: string;
  university: string | null;
  currency: string;
  study_years: number;
  annual_tuition: number;
  total_direct_cost: number;
  opportunity_cost: number;
  total_investment: number;
  estimated_start_salary: number;
  baseline_annual_salary: number;
  inflation_percent: number | null;
  job_search_months: number;
  horizon_years: number;
  roi_percent: number | null;
  payback_months: number | null;
  payback_from_enrollment_months: number | null;
  target_payback_years: number | null;
  payback_within_target: boolean | null;
  payback_target_gap_months: number | null;
  scenarios: TrialProjectionScenario[];
  trajectory: TrialProjectionYear[];
  sources: TrialProjectionSource[];
};

export type TrialProjectionScenario = {
  scenario: "pessimistic" | "base" | "optimistic";
  start_salary: number;
  roi_percent: number | null;
  payback_months: number | null;
};

export type TrialProjectionSource = {
  metric: string;
  source_name: string;
  source_reference: string | null;
  sample_size: number | null;
  confidence: string | null;
};

export type TrialProjectionYear = {
  year: number;
  target_salary: number;
  baseline_salary: number;
  cumulative_incremental_earnings: number;
};

export type TrialShowcaseGrant = {
  label: string;
  grant: number;
  without_grant: TrialProjectionResponse;
  with_grant: TrialProjectionResponse;
};

/** Public landing data: only real engine results; a case without stored data is left out. */
export type TrialShowcaseResponse = {
  careers: TrialProjectionOption[];
  scenarios: TrialShowcaseScenario[];
  grant_example: TrialShowcaseGrant | null;
};

export type TrialShowcaseScenario = {
  key: string;
  label: string;
  result: TrialProjectionResponse;
};

export type TuitionSnapshotResponse = {
  id: number;
  scope: string;
  country: string;
  university: string | null;
  program: string | null;
  degree: string | null;
  study_mode: string | null;
  student_residency: string;
  institution_type: string | null;
  academic_year: string;
  snapshot_date: IsoDate;
  currency: string;
  annual_tuition_min: number;
  annual_tuition: number;
  annual_tuition_max: number;
  mandatory_fees: number | null;
  sources: TuitionSnapshotSource[];
  acquired_at: IsoDateTime;
  confidence: string;
  methodology_version: string;
  validation_status: string;
  fingerprint: string;
  created_at: IsoDateTime;
};

export type TuitionSnapshotSource = {
  name: string;
  reference: string;
  url: string | null;
  acquired_at: IsoDateTime;
};

export type UniversityAddress = {
  street: string | null;
  postal_code: string | null;
  city: string | null;
  source: string;
  source_url: string;
};

export type UniversityFeeItem = {
  programme: string;
  faculty: string | null;
  level: string | null;
  study_mode: string | null;
  amount_per_year: number;
};

/** Yearly fees copied from one document; "press" means a published list, not the original order. */
export type UniversityFees = {
  academic_year: string;
  currency: string;
  source_kind: "official" | "press";
  source_title: string;
  source_url: string;
  min_per_year: number;
  max_per_year: number;
  cheapest: UniversityFeeItem;
  most_expensive: UniversityFeeItem;
  paid_programme_count: number;
  free_programme_count: number;
  programmes: UniversityFeeItem[];
};

export type UniversityProfileFacts = {
  founded: string | null;
  students: number | null;
  staff: number | null;
  city: string | null;
  logo_url: string | null;
  image_url: string | null;
};

export type UniversityProfileImage = {
  title: string;
  url: string;
  thumb_url: string;
  source_url: string;
};

export type UniversityProfileLink = {
  title: string;
  url: string;
};

/** A sentence or list item copied from an official page, never rewritten. */
export type UniversityProfileMention = {
  text: string;
  source_url: string;
};

export type UniversityProfileNewsItem = {
  title: string;
  url: string;
  published_at: IsoDateTime | null;
  source: string | null;
};

export type UniversityProfileOfficialPage = {
  title: string;
  url: string;
  kind: "admissions" | "scholarships" | "fees" | "sport" | "faculties" | "international" | "news";
};

export type UniversityProfileResponse = {
  status: "ready" | "partial" | "unavailable";
  fetched_at: IsoDateTime | null;
  summary: string | null;
  summary_source_url: string | null;
  wikidata_url: string | null;
  facts: UniversityProfileFacts;
  faculties: string[];
  official_pages: UniversityProfileOfficialPage[];
  admission_documents: UniversityProfileMention[];
  scholarship_mentions: UniversityProfileMention[];
  tuition_mentions: UniversityProfileTuitionMention[];
  sport_mentions: UniversityProfileMention[];
  news: UniversityProfileNewsItem[];
  videos: UniversityProfileNewsItem[];
  gallery: UniversityProfileImage[];
  sources: UniversityProfileLink[];
  unavailable_sources: string[];
};

/** Amount parsed deterministically from an official fees page; verify before relying on it. */
export type UniversityProfileTuitionMention = {
  text: string;
  source_url: string;
  amount: number;
  currency: string;
  period: "year" | "semester" | "month" | "unknown";
};

export type UniversityVerifiedFacts = {
  address: UniversityAddress;
  founded: string | null;
  faculties: string[];
  faculties_source: string | null;
  programme_count: number;
  fees: UniversityFees | null;
};

export type WorkspaceCourseResponse = {
  id: string;
  title: string;
  description: string;
  level: string;
  language: string;
  format: string;
  duration: string;
  skills: string[];
  provider_name: string;
  provider_url: string | null;
  saved: boolean;
};

export type WorkspacePreferences = {
  language: "English" | "\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430";
  currency: "Local" | "USD" | "EUR" | "PLN" | "GBP" | "UAH";
  theme: "Fence default" | "Dark" | "Monochrome";
};

export type WorkspaceProfile = {
  field_of_study: string;
  country: string;
  about: string;
  skills: string[];
  career_target: string | null;
};

export type WorkspaceResourceResponse = {
  id: string;
  title: string;
  description: string;
  source: "Public web" | "YouTube";
  url: string;
  skills: string[];
};

export type WorkspaceRoadmapSummary = {
  id: number;
  target_job: string;
  updated_at: IsoDateTime;
  plan: Record<string, unknown>;
};

export type WorkspaceStateResponse = {
  user: WorkspaceUser;
  profile: WorkspaceProfile;
  preferences: WorkspacePreferences;
  connections: Record<string, Record<string, unknown>>;
  saved_course_ids: string[];
  roadmap: WorkspaceRoadmapSummary | null;
};

export type WorkspaceUniversityDetailsResponse = {
  id: string;
  name: string;
  country: string;
  city: string | null;
  website: string | null;
  description: string | null;
  annual_tuition: number | null;
  currency: string | null;
  duration_years: number | null;
  study_mode: string | null;
  program_name: string | null;
  data_quality: "database" | "directory" | "illustrative";
  verified_facts: UniversityVerifiedFacts | null;
  fee_min: number | null;
  fee_max: number | null;
  fee_currency: string | null;
  programme_count: number | null;
  programmes: Record<string, unknown>[];
  documents: Record<string, unknown>[];
  scholarships: Record<string, unknown>[];
  profile: UniversityProfileResponse | null;
};

export type WorkspaceUniversityResponse = {
  id: string;
  name: string;
  country: string;
  city: string | null;
  website: string | null;
  description: string | null;
  annual_tuition: number | null;
  currency: string | null;
  duration_years: number | null;
  study_mode: string | null;
  program_name: string | null;
  data_quality: "database" | "directory" | "illustrative";
  verified_facts: boolean;
  fee_min: number | null;
  fee_max: number | null;
  fee_currency: string | null;
  programme_count: number | null;
};

export type WorkspaceUser = {
  id: number;
  username: string;
  email: string;
  plan: string;
  scenario_count: number;
  scenario_limit: number | null;
};


// ---- Requests ----

export type CheckoutRequest = {
  plan: "pro" | "business" | "enterprise";
  cycle: "monthly" | "yearly";
};

export type LoginSchema = {
  email: string;
  password: string;
};

/** Explicit, auditable policy for resolving one validated market snapshot. */
export type MarketSnapshotSelection = {
  seniority: string;
  as_of_date?: IsoDate;
  max_age_days?: number;
  minimum_confidence?: "low" | "medium" | "high";
};

export type PasswordResetRequestSchema = {
  email: string;
};

export type PasswordResetSchema = {
  code: string;
  new_password: string;
};

/** One visible line of the investment. Switched off, it counts as nothing. */
export type ProjectionCostItemInput = {
  key: "tuition" | "mandatory_fees" | "housing" | "food" | "transport" | "study_materials" | "other_living" | "additional_training" | "scholarships" | "pay_given_up" | "income_during_study";
  label: string;
  amount: number;
  per_month?: number | null;
  enabled?: boolean;
  editable?: boolean;
  source?: "user" | "country_average" | "calculated" | "stored" | "ai";
  source_name?: string | null;
  source_url?: string | null;
};

/** Походження конкретного показника; валідна форма не підтверджує правдивість джерела. */
export type ProjectionEvidenceInput = {
  metric: "target_start_salary" | "baseline_salary" | "salary_growth" | "tuition" | "mandatory_fees" | "scholarships" | "study_income" | "inflation" | "career_level";
  source_name: string;
  source_reference: string;
  acquired_at: IsoDateTime;
  country: string;
  role: string;
  seniority: string;
  currency: string;
  sample_size?: number | null;
  confidence: "low" | "medium" | "high";
};

export type RegisterSchema = {
  email: string;
  password: string;
  confirm_password?: string | null;
};

export type RoadmapPreviewRequest = {
  target_job: string;
  current_level?: "Beginner" | "Intermediate" | "Advanced";
  hours_per_week?: number;
  skills?: string[];
};

export type RoadmapTaskUpdate = {
  completed: boolean;
};

/** Вхідні умови освіти й кар'єри; після вибору tuition зберігаються в ревізії. */
export type SimulationAssumptionsInput = {
  university?: string | null;
  specialization?: string | null;
  country: string;
  degree: string;
  currency?: string;
  annual_tuition?: number | null;
  study_duration_years: number;
  career_target: string;
  existing_skills?: string[];
  additional_education?: string[];
  courses?: string[];
  certifications?: string[];
  experience_years?: number;
};

/** Створення сценарію: ручна ціна або одне джерело tuition, без змішування. */
export type SimulationCreateRequest = {
  name: string;
  assumptions: SimulationAssumptionsInput;
  tuition_snapshot_id?: number | null;
  tuition_snapshot_selection?: TuitionSnapshotSelection | null;
};

/** Умови фінансового прогнозу: рівно одне джерело зарплати та явний baseline. */
export type SimulationProjectionRequest = {
  market_snapshot_id?: number | null;
  market_snapshot_selection?: MarketSnapshotSelection | null;
  annual_start_salary?: number | null;
  baseline_annual_salary: number;
  annual_salary_growth_percent?: number;
  baseline_salary_growth_percent?: number;
  foregone_income_percent?: number;
  mandatory_fees?: number;
  scholarships_and_grants?: number;
  additional_education_cost?: number;
  incremental_living_cost?: number;
  /** Optional total gross income earned during the full study period. */
  employment_income_during_study?: number | null;
  horizon_years?: number;
  discount_rate_percent?: number | null;
  inflation_percent?: number | null;
  job_search_months?: number;
  employment_probability_percent?: number;
  target_payback_years?: number | null;
  evidence?: ProjectionEvidenceInput[];
  auto_assumptions?: boolean;
  cost_items?: ProjectionCostItemInput[];
  career_ladder?: number[] | null;
};

/** Anonymous trial calculation: the full engine on stored PL/UA data, nothing is saved. */
export type TrialProjectionRequest = {
  country: "Poland" | "Ukraine";
  career_target: string;
  university?: string | null;
  study_years?: number;
  annual_tuition?: number;
  job_search_months?: number;
  target_payback_years?: number | null;
};

/** Пошук збереженої ціни: точність, давність і довіра; без live API викликів. */
export type TuitionSnapshotSelection = {
  university: string;
  program: string;
  country: string;
  degree?: string | null;
  study_mode?: string | null;
  student_residency?: "domestic" | "international" | "eu" | "non_eu" | "in_state" | "out_of_state" | "unspecified";
  institution_type?: "public" | "private" | "other" | null;
  currency: string;
  as_of_date?: IsoDate;
  max_age_days?: number;
  minimum_confidence?: "low" | "medium" | "high";
  allow_country_fallback?: boolean;
};

export type WorkspacePreferencesInput = {
  language?: "English" | "\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430";
  currency?: "Local" | "USD" | "EUR" | "PLN" | "GBP" | "UAH";
  theme?: "Fence default" | "Dark" | "Monochrome";
};

export type WorkspaceProfileInput = {
  field_of_study?: string;
  country?: string;
  about?: string;
  skills?: string[];
  career_target?: string | null;
};

export type WorkspaceProfileUpdate = {
  username?: string | null;
  profile: WorkspaceProfileInput;
};
