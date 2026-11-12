"use client";

import { useEffect, useRef, useState } from "react";
import { formatRoiPerYear, toDisplay } from "@/lib/api/decimal";
import type { ProjectionCostItem, SimulationProjectionResponse } from "@/lib/api/generated";

/* Charts for a saved calculation. Every value is read from the stored deterministic projection;
   nothing here recalculates or estimates. Hover (or tap) shows the exact numbers per year. */

type Projection = SimulationProjectionResponse;
type Money = (value: number | null | undefined) => string;

const SCENARIO_LABEL: Record<string, string> = { pessimistic: "Pessimistic", base: "Base", optimistic: "Optimistic" };
const COST_PARTS = [
  { key: "tuition", label: "Tuition", tone: "ink" },
  { key: "mandatory_fees", label: "Mandatory fees", tone: "violet-deep" },
  { key: "additional_education", label: "Additional training", tone: "lime-deep" },
  { key: "incremental_living_cost", label: "Extra living costs", tone: "violet" },
  { key: "opportunity_cost", label: "Pay given up while studying", tone: "lime" },
] as const;

type MixPart = { key: string; label: string; tone: string; value: number; color?: string };
const LIVING_SHADES: Record<string, string> = { housing: "#a78bfa", food: "#bfa8ff", transport: "#d7c7ff", study_materials: "#e4daff", other_living: "#efe9ff" };

const compact = (value: number) => new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(value);
// Axis labels in the display currency chosen in Settings; positions stay on the stored values.
let axisCurrency = "";
const axis = (value: number) => compact(toDisplay(value, axisCurrency)[0]);

function useWidth<T extends HTMLElement>(fallback = 640) {
  const ref = useRef<T | null>(null);
  const [width, setWidth] = useState(fallback);
  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(260, Math.round(entry.contentRect.width))));
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  return [ref, width] as const;
}

/* Linear scale with "nice" ticks so the axis reads in round numbers. */
function scale(min: number, max: number, from: number, to: number) {
  const span = max - min || 1;
  return (value: number) => from + ((value - min) / span) * (to - from);
}
function niceTicks(min: number, max: number, count = 4) {
  const span = max - min || 1;
  const raw = span / count;
  const power = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * power).find((m) => m >= raw) ?? raw;
  const ticks: number[] = [];
  // Run from the step below the minimum to the step at or above the maximum, so no data point sits outside the axis.
  const first = Math.floor(min / step), last = Math.ceil(max / step);
  for (let i = first; i <= last; i += 1) ticks.push(Number((i * step).toFixed(6)));
  return ticks;
}

/* 1. Net position: what the degree has paid back, year by year, against the investment. */
function PaybackCurve({ projection, money }: { projection: Projection; money: Money }) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);
  const height = 260, pad = { top: 22, right: 18, bottom: 34, left: 58 };
  const points = [{ year: 0, net: -projection.total_investment }, ...projection.salary_trajectory.map((p) => ({ year: p.year, net: p.cumulative_incremental_earnings - projection.total_investment }))];
  const ticks = niceTicks(Math.min(0, ...points.map((p) => p.net)), Math.max(0, ...points.map((p) => p.net)));
  const x = scale(0, points.at(-1)?.year || 1, pad.left, width - pad.right);
  const y = scale(ticks[0], ticks.at(-1)!, height - pad.bottom, pad.top);
  const line = points.map((p, i) => `${i ? "L" : "M"}${x(p.year).toFixed(1)},${y(p.net).toFixed(1)}`).join(" ");
  const paybackYears = projection.payback_months == null ? null : projection.payback_months / 12;
  const target = projection.target_payback_years;
  const active = hover == null ? null : points[hover];

  return (
    <figure className="cc-card cc-card--dark cc-wide">
      <figcaption>
        <strong>When the degree pays for itself</strong>
        <span>Net position after graduating: extra earnings so far minus the total investment of {money(projection.total_investment)}.</span>
      </figcaption>
      <ul className="cc-legend cc-legend--explained">
        <li><i className="is-lime" /><span><b>Below zero</b> · the degree is still paying itself back</span></li>
        <li><i className="is-zero" /><span><b>Crossing zero</b> · payback: everything spent is earned back</span></li>
      </ul>
      <div className="cc-plot" ref={ref} onMouseLeave={() => setHover(null)}>
        <svg width={width} height={height} role="img" aria-label={paybackYears == null ? "The net position stays below zero within the horizon." : `The net position crosses zero after ${paybackYears.toFixed(1)} years.`}>
          <defs>
            <linearGradient id="cc-gain" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#b7ff2a" stopOpacity=".42" /><stop offset="1" stopColor="#b7ff2a" stopOpacity="0" /></linearGradient>
            <clipPath id="cc-above"><rect x="0" y="0" width={width} height={y(0)} /></clipPath>
          </defs>
          {ticks.map((t) => <g key={t}><line className={t === 0 ? "cc-zero" : "cc-gridline"} x1={pad.left} x2={width - pad.right} y1={y(t)} y2={y(t)} /><text className="cc-axis" x={pad.left - 8} y={y(t) + 4} textAnchor="end">{axis(t)}</text></g>)}
          {points.map((p) => <text key={p.year} className="cc-axis" x={x(p.year)} y={height - 12} textAnchor="middle">{p.year === 0 ? "grad" : `y${p.year}`}</text>)}
          <path d={`${line} L${x(points.at(-1)!.year)},${y(0)} L${x(0)},${y(0)} Z`} fill="url(#cc-gain)" clipPath="url(#cc-above)" />
          {target != null && target <= (points.at(-1)?.year || 0) && <g><line className="cc-target" x1={x(target)} x2={x(target)} y1={pad.top} y2={height - pad.bottom} /><text className="cc-note" x={x(target) + 6} y={pad.top + 10}>your {target}-year target</text></g>}
          <path d={line} className="cc-line cc-line--lime" />
          {paybackYears != null && paybackYears <= (points.at(-1)?.year || 0) && <g className="cc-payback"><circle cx={x(paybackYears)} cy={y(0)} r="7" /><text className="cc-note cc-note--strong" x={x(paybackYears) - 12} y={y(0) - 14} textAnchor="end">pays back · {paybackYears.toFixed(1)} yrs</text></g>}
          {points.map((p, i) => <circle key={p.year} className={`cc-dot ${hover === i ? "is-on" : ""}`} cx={x(p.year)} cy={y(p.net)} r={hover === i ? 6 : 4} />)}
          {active && <line className="cc-cross" x1={x(active.year)} x2={x(active.year)} y1={pad.top} y2={height - pad.bottom} />}
          {points.map((p, i) => <rect key={p.year} className="cc-hit" x={x(p.year) - (width / points.length) / 2} y={0} width={width / points.length} height={height} onMouseEnter={() => setHover(i)} onClick={() => setHover(i)} />)}
        </svg>
        {active && <div className="cc-tip" style={{ left: Math.min(Math.max(x(active.year), 90), width - 90) }}><b>{active.year === 0 ? "At graduation" : `Year ${active.year} after graduating`}</b><span>{active.net >= 0 ? "Ahead by" : "Still to recover"} {money(Math.abs(active.net))}</span></div>}
      </div>
    </figure>
  );
}

/* Career levels the forecast used: the start level plus later levels with market data (career_level evidence).
   Years 1-2 after graduating are junior, 3-5 mid, 6+ senior, matching the server's ladder. */
const LEVEL_YEARS: Record<string, number> = { junior: 2, mid: 3 };
const LEVEL_NAME: Record<string, string> = { junior: "Junior", mid: "Middle", senior: "Senior" };
function careerBands(projection: Projection): { level: string; from: number; to: number }[] {
  const start = projection.evidence.find((item) => item.metric === "target_start_salary")?.seniority?.toLowerCase();
  const later = projection.evidence.filter((item) => item.metric === "career_level").map((item) => item.seniority.toLowerCase());
  if (!start || !(start in LEVEL_NAME) || !later.length) return [];
  const levels = [start, ...later.filter((level) => level !== start)];
  const horizon = projection.salary_trajectory.at(-1)?.year ?? projection.horizon_years;
  const bands: { level: string; from: number; to: number }[] = [];
  let from = 1;
  levels.forEach((level, index) => {
    const to = index === levels.length - 1 ? horizon : Math.min(horizon, from + (LEVEL_YEARS[level] ?? horizon) - 1);
    if (from <= horizon) bands.push({ level, from, to });
    from = to + 1;
  });
  return bands;
}

/* 2. Salary with the degree against the pay without it. */
function SalaryPaths({ projection, money }: { projection: Projection; money: Money }) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);
  const bands = careerBands(projection);
  const height = 260, pad = { top: bands.length ? 34 : 18, right: 86, bottom: 34, left: 58 };
  const data = projection.salary_trajectory;
  if (!data.length) return null;
  const inputs = projection.calculation_inputs;
  const searchMonths = inputs?.job_search_months ?? 0;
  const jobChance = inputs?.employment_probability_percent;
  const ticks = niceTicks(0, Math.max(...data.flatMap((p) => [p.target_salary, p.baseline_salary])));
  const x = scale(data[0].year, data.at(-1)!.year === data[0].year ? data[0].year + 1 : data.at(-1)!.year, pad.left, width - pad.right);
  const y = scale(0, ticks.at(-1)!, height - pad.bottom, pad.top);
  const path = (key: "target_salary" | "baseline_salary") => data.map((p, i) => `${i ? "L" : "M"}${x(p.year).toFixed(1)},${y(p[key]).toFixed(1)}`).join(" ");
  const last = data.at(-1)!;
  const active = hover == null ? null : data[hover];

  return (
    <figure className="cc-card cc-card--dark">
      <figcaption>
        <strong>Salary with and without the degree</strong>
        <span>Yearly pay after graduating, in today&apos;s money. The gap between the two lines is what pays the degree back.</span>
      </figcaption>
      <ul className="cc-legend cc-legend--explained">
        <li><i className="is-lime" /><span><b>With the degree</b> · market pay in your target career{bands.length ? `, growing ${bands.map((band) => LEVEL_NAME[band.level]).join(" → ")} with experience` : ""}</span></li>
        <li><i className="is-violet is-dashed" /><span><b>Without it</b> · the official typical pay you would earn instead</span></li>
      </ul>
      <div className="cc-plot" ref={ref} onMouseLeave={() => setHover(null)}>
        <svg width={width} height={height} role="img" aria-label={`Starting salary ${money(data[0].target_salary)} with the degree against ${money(data[0].baseline_salary)} without it.`}>
          {bands.map((band, index) => {
            const left = index === 0 ? pad.left : (x(band.from - 1) + x(band.from)) / 2;
            const right = index === bands.length - 1 ? width - pad.right : (x(band.to) + x(band.to + 1)) / 2;
            return <g key={band.level}>
              <rect className={`cc-band ${index % 2 ? "is-alt" : ""}`} x={left} y={pad.top - 4} width={Math.max(0, right - left)} height={height - pad.bottom - pad.top + 4} />
              <text className="cc-band-label" x={(left + right) / 2} y={pad.top - 12} textAnchor="middle">
                {right - left < 56 ? LEVEL_NAME[band.level][0] : right - left < 110 ? LEVEL_NAME[band.level] : `${LEVEL_NAME[band.level]} · y${band.from}${band.to > band.from ? `–${band.to}` : ""}`}
              </text>
            </g>;
          })}
          {ticks.map((t) => <g key={t}><line className={t === 0 ? "cc-zero" : "cc-gridline"} x1={pad.left} x2={width - pad.right} y1={y(t)} y2={y(t)} /><text className="cc-axis" x={pad.left - 8} y={y(t) + 4} textAnchor="end">{axis(t)}</text></g>)}
          {data.map((p) => <text key={p.year} className="cc-axis" x={x(p.year)} y={height - 12} textAnchor="middle">y{p.year}</text>)}
          <path d={path("baseline_salary")} className="cc-line cc-line--violet cc-line--dashed" />
          <path d={path("target_salary")} className="cc-line cc-line--lime" />
          <text className="cc-end cc-end--lime" x={x(last.year) + 8} y={y(last.target_salary) + 4}>{axis(last.target_salary)}</text>
          <text className="cc-end cc-end--violet" x={x(last.year) + 8} y={y(last.baseline_salary) + 4}>{axis(last.baseline_salary)}</text>
          {active && <><line className="cc-cross" x1={x(active.year)} x2={x(active.year)} y1={pad.top} y2={height - pad.bottom} /><circle className="cc-dot is-on" cx={x(active.year)} cy={y(active.target_salary)} r="6" /><circle className="cc-dot cc-dot--violet is-on" cx={x(active.year)} cy={y(active.baseline_salary)} r="6" /></>}
          {data.map((p, i) => <rect key={p.year} className="cc-hit" x={x(p.year) - (width / data.length) / 2} y={0} width={width / data.length} height={height} onMouseEnter={() => setHover(i)} onClick={() => setHover(i)} />)}
        </svg>
        {active && <div className="cc-tip" style={{ left: Math.min(Math.max(x(active.year), 90), width - 90) }}><b>Year {active.year}{bands.find((band) => active.year >= band.from && active.year <= band.to) ? ` · ${LEVEL_NAME[bands.find((band) => active.year >= band.from && active.year <= band.to)!.level]}` : ""}</b><span>With the degree {money(active.target_salary)}</span><span>Without it {money(active.baseline_salary)}</span><span>Difference {money(active.incremental_earnings)}</span></div>}
      </div>
      <p className="cc-footnote">
        {searchMonths ? `Year 1 is lower: about ${searchMonths} months of job search with no pay. ` : ""}
        {jobChance != null && jobChance < 100 ? `The lime line also allows for a ${100 - jobChance}% chance of not finding a job in the field. ` : ""}
        {bands.length ? "Pay at each level is the median of current listings for that level." : "Fence has no pay data for later career levels of this role yet, so the line stays at the starting pay."}
      </p>
    </figure>
  );
}

/* 3. What the investment is made of (part-to-whole, one stacked bar + labelled legend). */
function InvestmentMix({ projection, money, lines }: { projection: Projection; money: Money; lines?: ProjectionCostItem[] }) {
  const [hover, setHover] = useState<string | null>(null);
  const breakdown = projection.cost_breakdown as Record<string, number | null>;
  // Living costs show as their own lines (housing, food…) when the calculation has them.
  const living = (lines ?? []).filter((line) => line.enabled && line.amount > 0 && line.key in LIVING_SHADES);
  const parts = COST_PARTS.flatMap((part): MixPart[] =>
    part.key === "incremental_living_cost" && living.length
      ? living.map((line) => ({ key: line.key, label: line.label, tone: "violet", value: line.amount, color: LIVING_SHADES[line.key] }))
      : [{ key: part.key, label: part.label, tone: part.tone, value: Math.max(0, breakdown[part.key] ?? 0) }]).filter((part) => part.value > 0);
  const total = parts.reduce((sum, part) => sum + part.value, 0);
  const grants = breakdown.scholarships_and_grants ?? 0;
  if (!total) return null;

  return (
    <figure className="cc-card">
      <figcaption>
        <strong>What the investment is made of</strong>
        <span>{money(projection.total_investment)} in total{grants > 0 ? `, after ${money(grants)} of scholarships and grants` : ""}.</span>
      </figcaption>
      <div className="cc-stack" role="img" aria-label={parts.map((part) => `${part.label} ${Math.round((part.value / total) * 100)}%`).join(", ")}>
        {parts.map((part) => <i key={part.key} className={`is-${part.tone} ${hover && hover !== part.key ? "is-dim" : ""}`} style={{ flexGrow: part.value, ...(part.color ? { background: part.color } : {}) }} onMouseEnter={() => setHover(part.key)} onMouseLeave={() => setHover(null)} title={`${part.label}: ${money(part.value)}`} />)}
      </div>
      <ul className="cc-mix">
        {parts.map((part) => <li key={part.key} className={hover === part.key ? "is-on" : ""} onMouseEnter={() => setHover(part.key)} onMouseLeave={() => setHover(null)}><i className={`is-${part.tone}`} style={part.color ? { background: part.color } : undefined} /><span>{part.label}</span><b>{money(part.value)}</b><em>{Math.round((part.value / total) * 100)}%</em></li>)}
      </ul>
    </figure>
  );
}

/* 4. Payback in each salary scenario (one measure, one hue; the base case is highlighted). */
function ScenarioBars({ projection, money }: { projection: Projection; money: Money }) {
  const items = projection.scenario_outcomes;
  if (items.length < 2) return null;
  const horizon = projection.horizon_years * 12;
  return (
    <figure className="cc-card">
      <figcaption>
        <strong>Payback in each salary scenario</strong>
        <span>Shorter bar, faster payback. Bars run to the {projection.horizon_years}-year horizon.</span>
      </figcaption>
      <ul className="cc-bars">
        {items.map((item) => {
          const reached = item.payback_months != null;
          const share = reached ? Math.min(1, item.payback_months! / horizon) : 1;
          return (
            <li key={item.scenario} className={`is-${item.scenario} ${reached ? "" : "is-never"}`}>
              <span>{SCENARIO_LABEL[item.scenario]}<small>{money(item.start_salary)} start</small></span>
              <div className="cc-bar-track"><i style={{ width: `${Math.max(4, share * 100)}%` }} /></div>
              <b>{reached ? `${(item.payback_months! / 12).toFixed(1)} yrs` : "not reached"}<small>ROI {formatRoiPerYear(item.roi_percent, projection.horizon_years)}</small></b>
            </li>
          );
        })}
      </ul>
    </figure>
  );
}

export default function CalculationCharts({ projection, money, lines }: { projection: Projection; money: Money; lines?: ProjectionCostItem[] }) {
  axisCurrency = projection.currency;
  if (!projection.salary_trajectory.length) return null;
  return (
    <section id="charts" className="cc-grid" aria-label="Calculation charts">
      <PaybackCurve projection={projection} money={money} />
      <SalaryPaths projection={projection} money={money} />
      <InvestmentMix projection={projection} money={money} lines={lines} />
      <ScenarioBars projection={projection} money={money} />
    </section>
  );
}
