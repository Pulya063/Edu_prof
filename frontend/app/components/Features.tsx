import { useEffect, useMemo, useRef, useState, type CSSProperties, type KeyboardEvent } from "react";
import Image from "next/image";
import Link from "next/link";
import { ApiRequestError } from "@/lib/api/client";
import { runTrialProjection, type TrialProjectionResponse } from "@/lib/api/trial";
import { formatMoney, formatRoi, formatYears, useLandingData } from "../context/LandingDataContext";
import { useCarouselGestures } from "../hooks/useCarouselGestures";
import { HeadlineLine } from "../hooks/useScrollMotion";
import { createScreenProjection } from "../utils/screenProjection";
import { useScaledFrame } from "../hooks/useScaledFrame";
import CoverageMap from "./CoverageMap";

function Arrow({ direction = "right" }: { direction?: "left" | "right" }) {
  const right = direction === "right";
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" focusable="false">
      <path d={right ? "M5 12h14m-6-6 6 6-6 6" : "M19 12H5m6 6-6-6 6-6"} stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

const COMPARISON_KEYS = ["warsaw-python", "knu-python", "warsaw-law"] as const;
const COMPARISON_LOOK = [{ icon: "campus", tone: "dark" }, { icon: "globe", tone: "light" }, { icon: "spark", tone: "lime" }] as const;
const SCALE_MONTHS = 120;

const paybackShare = (months: number | null) => (months === null ? 100 : Math.min(100, (months / SCALE_MONTHS) * 100));

function verdictText(result: TrialProjectionResponse) {
  const gap = result.payback_target_gap_months;
  if (result.target_payback_years === null) return null;
  if (result.payback_within_target) return gap ? `Pays back ${Math.abs(gap)} months before a ${result.target_payback_years}-year target` : `Pays back right on a ${result.target_payback_years}-year target`;
  return gap === null ? "No payback within 10 years" : `Pays back ${gap} months after a ${result.target_payback_years}-year target`;
}

function SymbolIcon({ kind }: { kind: string }) {
  const paths: Record<string, string> = {
    campus: "M4 20V9l8-6 8 6v11M3 20h18M9 20v-7h6v7",
    globe: "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20ZM2 12h20M12 2c-5 5-5 15 0 20M12 2c5 5 5 15 0 20",
    spark: "m12 2 2.2 7.8L22 12l-7.8 2.2L12 22l-2.2-7.8L2 12l7.8-2.2L12 2Z",
    pin: "M12 21s7-6.1 7-12a7 7 0 0 0-14 0c0 5.9 7 12 7 12ZM12 6a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z",
    degree: "m2 9 10-5 10 5-10 5L2 9Zm4 3v5c4 3 8 3 12 0v-5M22 9v7",
    experience: "M4 7h16v13H4V7Zm5 0V4h6v3M4 13h16M11 12h2v3h-2z",
    ai: "M12 3v4m0 10v4M3 12h4m10 0h4M6 6l3 3m6 6 3 3M18 6l-3 3m-6 6-3 3M12 9l3 3-3 3-3-3 3-3Z",
    market: "M4 19V5m0 14h17M7 15l4-4 3 2 5-6M16 7h3v3",
    internship: "M5 20V4h14v16M3 20h18M9 8h6M9 12h6M10 20v-4h4v4",
    grant: "m12 2 2.6 6.4L21 11l-6.4 2.6L12 20l-2.6-6.4L3 11l6.4-2.6L12 2Z",
    digital: "M3 5h18v12H3V5Zm6 16h6M12 17v4M7 9h4m-2-2v4",
    women: "M12 3a6 6 0 1 0 0 12 6 6 0 0 0 0-12Zm0 12v7m-4-3h8",
    local: "M12 21s7-6.1 7-12a7 7 0 0 0-14 0c0 5.9 7 12 7 12ZM9 9h6m-3-3v6",
  };
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false"><path d={paths[kind] ?? paths.spark} /></svg>;
}

const defaultScreenCorners = [
  // Extend slightly beneath the bezel so no green edge remains visible.
  { x: 61.5, y: 277 },
  { x: 496.2, y: 105.1 },
  { x: 646.2, y: 428 },
  { x: 216.7, y: 630.7 },
] as const;

export function LiveRoiCalculator() {
  const { data, status, scenario } = useLandingData();
  const careers = useMemo(() => data?.careers ?? [], [data]);
  const countries = useMemo(() => Array.from(new Set(careers.map((item) => item.country))), [careers]);
  const [country, setCountry] = useState("Poland");
  const [career, setCareer] = useState("Python Backend Developer");
  const [tuition, setTuition] = useState(0);
  const [years, setYears] = useState(3.5);
  const [result, setResult] = useState<TrialProjectionResponse | null>(null);
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const { frameRef: calculatorFrameRef, scale: calculatorScale } = useScaledFrame<HTMLDivElement>(920);
  const screenProjection = createScreenProjection(defaultScreenCorners, 600, 440);

  const roles = careers.filter((item) => item.country === country);
  const currency = roles[0]?.currency ?? "PLN";
  const tuitionMax = currency === "UAH" ? 200000 : 50000;
  const shown = result ?? scenario("warsaw-python");
  const changed = (update: () => void) => { update(); setDirty(true); setError(""); };
  const chooseCountry = (value: string) => changed(() => {
    setCountry(value);
    setTuition(0);
    const same = careers.some((item) => item.country === value && item.career_target === career);
    if (!same) setCareer(careers.find((item) => item.country === value)?.career_target ?? "");
  });
  const calculate = async () => {
    setBusy(true); setError("");
    try {
      setResult(await runTrialProjection({ country: country as "Poland" | "Ukraine", career_target: career, university: null, study_years: years, annual_tuition: tuition, job_search_months: 3, target_payback_years: 5 }));
      setDirty(false);
    } catch (reason) {
      setError(reason instanceof ApiRequestError ? reason.message : "Could not calculate this scenario.");
    } finally {
      setBusy(false);
    }
  };
  const peak = shown ? Math.max(shown.total_investment, ...shown.trajectory.map((point) => point.cumulative_incremental_earnings), 1) : 1;
  const verdict = shown ? verdictText(shown) : null;

  return (
    <section className="feature-section calculator-section motion-section" id="calculator" data-motion-section="true" data-header-theme="light" aria-labelledby="calculator-title">
      <div className="feature-shell calculator-shell">
        <div className="feature-intro calculator-intro">
          <p className="feature-label"><i /> 02 / LIVE FORECAST</p>
          <h2 id="calculator-title"><HeadlineLine>Test the <span className="oval-highlight">value</span> before</HeadlineLine><HeadlineLine>you <span className="rect-highlight lime-marker">commit.</span></HeadlineLine></h2>
          <p className="feature-description">Set the country, career, tuition and study length, then press Calculate. Cost, payback and ten-year return come from the same engine and salary data as your saved scenarios.</p>
          <ul className="live-sources" aria-label="Data sources used"><li>World Bank CPI</li><li>Eurostat</li><li>Pracuj.pl</li><li>DOU survey</li></ul>
        </div>

        <div className="calculator-device-viewport">
          <div ref={calculatorFrameRef} className="calculator-device-frame" style={{ "--calculator-scale": calculatorScale } as CSSProperties}>
            <div className="calculator-board ipad-device" aria-label="Interactive education ROI calculator" style={{ "--calculator-screen-transform": screenProjection } as CSSProperties}>
              <Image className="calculator-device-art" src="/fence-ipad-keyboard.webp" alt="Floating iPad with keyboard displaying the education ROI calculator" width={1254} height={1254} quality={85} priority sizes="(max-width: 720px) 100vw, (max-width: 1180px) 92vw, 920px" />

              <aside className="calculator-rail" aria-hidden="true"><b>F</b><span> ROI calculator</span><span> Career paths</span><span> Compare</span><span> Saved scenarios</span></aside>
              <div className="calculator-main">
                <header><div><h3>Education ROI Calculator</h3><p>Real salary data for Poland and Ukraine.</p></div><span className="calculator-breadcrumb">Education / Outcomes / You</span></header>
                <div className="calculator-form">
                  <label className="calculator-field calculator-field--select">Country<div className="calculator-select-wrap"><select value={country} onChange={(event) => chooseCountry(event.target.value)}>{(countries.length ? countries : [country]).map((item) => <option key={item}>{item}</option>)}</select></div></label>
                  <label className="calculator-field calculator-field--range">Annual tuition ({currency})<output>{tuition === 0 ? "State-funded" : formatMoney(tuition, currency)}</output><input type="range" min="0" max={tuitionMax} step={tuitionMax / 100} value={tuition} style={{ "--range-progress": `${(tuition / tuitionMax) * 100}%` } as CSSProperties} onChange={(event) => { const value = Number(event.target.value); changed(() => setTuition(value)); }} /></label>
                  <label className="calculator-field calculator-field--range">Study length <output>{years} years</output><input type="range" min="1" max="6" step="0.5" value={years} style={{ "--range-progress": `${((years - 1) / 5) * 100}%` } as CSSProperties} onChange={(event) => { const value = Number(event.target.value); changed(() => setYears(value)); }} /></label>
                  <label className="calculator-field calculator-field--select">Career goal<div className="calculator-select-wrap"><select value={career} onChange={(event) => { const value = event.target.value; changed(() => setCareer(value)); }}>{(roles.length ? roles.map((item) => item.career_target) : [career]).map((item) => <option key={item}>{item}</option>)}</select></div></label>
                  <button type="button" className="calculate-button" disabled={busy || status !== "ready"} onClick={() => void calculate()}>{busy ? "Calculating…" : "Calculate ROI"} <Arrow /></button>
                </div>
                <div className="calculator-results" aria-live="polite">
                  <article className="roi-result"><span>Estimated 10-year ROI</span><strong>{shown ? formatRoi(shown.roi_percent) : "—"} <i></i></strong><small>{dirty ? "Inputs changed: press Calculate" : shown ? `${shown.career_target}, ${shown.country}` : "Waiting for live data"}</small></article>
                  <article className="payback-result"><span>Payback Period</span><strong>{shown ? (shown.payback_months === null ? "10y+" : `${shown.payback_months} months`) : "—"}</strong><small>{shown ? `On ${formatMoney(shown.total_investment, shown.currency)} invested` : ""}</small><i className="blur-orb" aria-hidden="true" /></article>
                  <article className="salary-result"><span>Median Starting Salary</span><strong>{shown ? formatMoney(shown.estimated_start_salary, shown.currency) : "—"}</strong><small>{shown ? "per year, from live data" : ""}</small><b aria-hidden="true"></b></article>
                </div>
              </div>
            </div>
          </div>
          {shown && (
            <aside className="live-calc-card" aria-live="polite">
              {verdict && <p className={`live-calc-verdict ${shown.payback_within_target ? "is-yes" : "is-no"}`}>{verdict}</p>}
              <h3>{shown.career_target}</h3>
              <small>{shown.country} · {shown.study_years} years · {shown.annual_tuition === 0 ? "state-funded place" : `${formatMoney(shown.annual_tuition, shown.currency)} / yr`}</small>
              <dl><div><dt>Payback</dt><dd>{shown.payback_months === null ? "10y+" : `${shown.payback_months} mo`}</dd></div><div><dt>10-year ROI</dt><dd>{formatRoi(shown.roi_percent)}</dd></div></dl>
              <div className="live-calc-bars" role="img" aria-label="Extra earnings for each year after graduating, against the investment">
                {shown.trajectory.map((point) => <i key={point.year} className={point.cumulative_incremental_earnings >= shown.total_investment ? "is-paid" : ""} style={{ height: `${Math.max(5, (Math.max(0, point.cumulative_incremental_earnings) / peak) * 100)}%` }} />)}
              </div>
              <small>Extra earnings by year after graduating. Lime: {formatMoney(shown.total_investment, shown.currency)} invested is covered.</small>
              {error && <p className="live-error" role="alert">{error}</p>}
              <Link className="live-link" href="/try">Open the full trial <Arrow /></Link>
            </aside>
          )}
          {!shown && status === "unavailable" && <p className="live-unavailable">Live salary data is being refreshed. Try again in a few minutes.</p>}
        </div>
      </div>
    </section>
  );
}

export function UniversityComparison() {
  const { status, scenario, data } = useLandingData();
  const options = COMPARISON_KEYS.flatMap((key, index) => {
    const result = scenario(key);
    const label = data?.scenarios.find((item) => item.key === key)?.label;
    return result && label ? [{ key, label, result, ...COMPARISON_LOOK[index] }] : [];
  });
  const fastest = options.reduce<number | null>((best, item) => (item.result.payback_months !== null && (best === null || item.result.payback_months < best) ? item.result.payback_months : best), null);
  const [active, setActive] = useState(0);
  const cardsRef = useRef<HTMLDivElement>(null);
  const scrollFrameRef = useRef<number | null>(null);
  const scrollReleaseRef = useRef<number | null>(null);
  const programmaticScrollRef = useRef(false);

  const selectUniversity = (index: number) => {
    setActive(index);
    if (!window.matchMedia("(max-width: 700px)").matches) return;
    programmaticScrollRef.current = true;
    const cards = cardsRef.current;
    const card = cards?.querySelector<HTMLElement>(`[data-university-index="${index}"]`);
    if (cards && card) cards.scrollTo({ left: card.offsetLeft - (cards.clientWidth - card.offsetWidth) / 2, behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    if (scrollReleaseRef.current !== null) window.clearTimeout(scrollReleaseRef.current);
    scrollReleaseRef.current = window.setTimeout(() => {
      programmaticScrollRef.current = false;
      scrollReleaseRef.current = null;
    }, 1400);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLElement>) => {
    if (e.key === "ArrowRight") {
      e.preventDefault();
      selectUniversity(Math.min(active + 1, options.length - 1));
    }
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      selectUniversity(Math.max(active - 1, 0));
    }
  };

  const syncActiveToScroll = () => {
    if (programmaticScrollRef.current) return;
    if (scrollFrameRef.current !== null) return;
    scrollFrameRef.current = window.requestAnimationFrame(() => {
      scrollFrameRef.current = null;
      const cards = cardsRef.current;
      if (!cards || cards.scrollWidth <= cards.clientWidth) return;
      const center = cards.scrollLeft + cards.clientWidth / 2;
      const next = options.reduce((closest, _, index) => {
        const candidate = cards.querySelector<HTMLElement>(`[data-university-index="${index}"]`);
        const current = cards.querySelector<HTMLElement>(`[data-university-index="${closest}"]`);
        if (!candidate || !current) return closest;
        const candidateCenter = candidate.offsetLeft + candidate.offsetWidth / 2;
        const currentCenter = current.offsetLeft + current.offsetWidth / 2;
        return Math.abs(candidateCenter - center) < Math.abs(currentCenter - center) ? index : closest;
      }, active);
      setActive((current) => current === next ? current : next);
    });
  };

  useEffect(() => () => {
    if (scrollFrameRef.current !== null) window.cancelAnimationFrame(scrollFrameRef.current);
    if (scrollReleaseRef.current !== null) window.clearTimeout(scrollReleaseRef.current);
  }, []);

  const gesturesRef = useCarouselGestures<HTMLDivElement>((direction) => {
    if (options.length) selectUniversity((active + direction + options.length) % options.length);
  }, ".university-cards");

  return (
    <section className="feature-section comparison-section dark-feature motion-section" id="comparison" data-motion-section="true" data-header-theme="dark" aria-labelledby="comparison-title" tabIndex={0} onKeyDown={onKeyDown}>
      <div className="feature-shell comparison-shell">
        <div className="feature-intro dark-intro">
          <p className="feature-label">03 / EDUCATION PATH COMPARISON</p>
          <h2 id="comparison-title"><HeadlineLine>Compare <span className="oval-highlight">more</span> than</HeadlineLine><HeadlineLine><span className="rect-highlight violet-marker">rankings.</span></HeadlineLine></h2>
          <p className="feature-description">A ranking tells you which university is famous. Fence shows which one pays back: tuition, funding, employment and salaries, side by side.</p>
          <div className="comparison-count"><strong>{String(options.length || COMPARISON_KEYS.length).padStart(2, "0")}</strong><span>Options</span><i /></div>
        </div>
        <div className="comparison-area" ref={gesturesRef}>
          <div className="university-cards" data-active={active} ref={cardsRef} onScroll={syncActiveToScroll}>
            {options.map((option, index) => {
              const { result } = option;
              return (
              <article className={`university-card university-card--${option.tone} ${active === index ? "is-active" : ""}`} key={option.key} aria-label={`${option.label}, ${active === index ? "selected" : "option"}`} data-university-index={index}>
                <button className="university-card-select" type="button" aria-label={`Select ${option.label}`} aria-pressed={active === index} onClick={() => selectUniversity(index)} />
                <span className="university-icon" aria-hidden="true"><SymbolIcon kind={option.icon} /></span>
                {result.payback_months !== null && result.payback_months === fastest && <span className="best-fit"><i aria-hidden="true"><SymbolIcon kind="spark" /></i> Fastest payback</span>}
                <h3>{option.label}</h3><p>{result.country} · {result.study_years} years of study</p>
                <dl id={`university-${index}`}><div><dt>Tuition</dt><dd>{result.annual_tuition === 0 ? "State-funded" : formatMoney(result.annual_tuition, result.currency)}</dd></div><div><dt>Start salary / yr</dt><dd>{formatMoney(result.estimated_start_salary, result.currency)}</dd></div><div><dt>Total investment</dt><dd>{formatMoney(result.total_investment, result.currency)}</dd></div><div><dt>Payback</dt><dd>{formatYears(result.payback_months)}</dd></div></dl>
                <div className="university-score"><span>Estimated 10-year ROI</span><strong>{formatRoi(result.roi_percent)}</strong><span>{result.payback_within_target ? "Within a 5-year target" : "Misses a 5-year target"}</span><i className="payback-scale"><em style={{ width: `${paybackShare(result.payback_months)}%` }} /><b aria-hidden="true" /></i><small>Payback on a 10-year scale; the mark is 5 years</small></div>
              </article>
              );
            })}
            {options.length === 0 && <p className="live-unavailable">{status === "loading" ? "Loading live scenarios…" : "Live salary data is being refreshed. Try again in a few minutes."}</p>}
          </div>
          <p className="comparison-method">Calculated on current salary data: all pay given up while studying, salaries in today&rsquo;s money, 3 months to the first job. <Link className="live-link" href="/try">Run your own numbers <Arrow /></Link></p>
        </div>
      </div>
      {options[active] && <p className="sr-only" aria-live="polite">Viewing {options[active].label}.</p>}
    </section>
  );
}

const factors = [
  { name: "Location", detail: "Where you live and work matters.", delta: "+$12,240", icon: "pin", salary: "$80,240" },
  { name: "Degree", detail: "Your field and level of study.", delta: "+$16,320", icon: "degree", salary: "$84,320" },
  { name: "Experience", detail: "More experience, higher earnings.", delta: "+$19,040", icon: "experience", salary: "$87,040" },
  { name: "AI impact", detail: "Understand how AI changes your field.", delta: "-$5,440", icon: "ai", salary: "$62,560" },
  { name: "Market demand", detail: "Stronger industries lift outcomes.", delta: "+$14,960", icon: "market", salary: "$82,960" },
  { name: "Internships", detail: "Real-world experience opens doors.", delta: "+$8,160", icon: "internship", salary: "$76,160" },
] as const;

export function OutcomeFactors() {
  const [selected, setSelected] = useState(5);
  const factor = factors[selected];
  const { data } = useLandingData();
  const [country, setCountry] = useState("Poland");
  const orbitRef = useCarouselGestures<HTMLDivElement>((direction) => setSelected((current) => (current + direction + factors.length) % factors.length));
  const medians = (data?.careers ?? []).filter((item) => item.country === country).sort((a, b) => b.median_salary - a.median_salary);
  const topMedian = medians[0]?.median_salary ?? 1;
  return (
    <section className="feature-section factors-section dark-feature motion-section" id="factors" data-motion-section="true" data-header-theme="dark" aria-labelledby="factors-title">
      <div className="feature-shell factors-shell">
        <div className="feature-intro dark-intro factors-intro"><p className="feature-label"><i /> 04 / WHAT SHAPES THE OUTCOME</p><h2 id="factors-title"><HeadlineLine>Your outcome</HeadlineLine><HeadlineLine>is shaped by</HeadlineLine><HeadlineLine><span className="oval-highlight">more</span> than</HeadlineLine><HeadlineLine>a degree.</HeadlineLine></h2><p className="feature-description">City, internships, experience and demand for the role can move your result more than the diploma itself. Tap a factor to see how. Figures here are illustrative.</p><a className="lime-button" href="/register">Build my path <span><Arrow /></span></a><div className="factor-proof"><b>6<small>decision factors</small></b><b>Scenario-based<small>salary assumptions</small></b><b>One view<small>of the trade-offs</small></b></div></div>
        <div className="factor-orbit" ref={orbitRef} aria-label="Interactive career outcome factors">
          <div className="orbit-circle orbit-circle--outer" aria-hidden="true" /><div className="orbit-circle orbit-circle--middle" aria-hidden="true" /><div className="orbit-circle orbit-circle--inner" aria-hidden="true" />
          <div className="salary-core" aria-live="polite"><span>Projected salary</span><strong>{factor.salary}</strong><small>Illustrative US data analyst benchmark</small></div>
          {factors.map((item, index) => <button className={`factor-card factor-card--${index} ${selected === index ? "is-selected" : ""}`} type="button" key={item.name} aria-pressed={selected === index} onClick={() => setSelected(index)}><i aria-hidden="true"><SymbolIcon kind={item.icon} /></i><span><b>{item.name}</b><small>{item.detail}</small></span><strong>{item.delta}</strong></button>)}
        </div>
        {medians.length > 0 && (
          <div className="live-medians">
            <header>
              <div><h3>What the market pays now</h3><p>Median salary per year from current adverts and surveys. These figures are real, not illustrative.</p></div>
              <div className="live-toggle" role="group" aria-label="Choose a country">{["Poland", "Ukraine"].map((item) => <button type="button" key={item} aria-pressed={country === item} onClick={() => setCountry(item)}>{item}</button>)}</div>
            </header>
            <ul>{medians.slice(0, 8).map((item) => <li key={item.career_target}><span>{item.career_target}<small>{item.salary_source === "official" ? "official estimate" : item.seniority === "junior" ? "junior" : "all levels"}</small></span><i><em style={{ width: `${(item.median_salary / topMedian) * 100}%` }} /></i><b>{formatMoney(item.median_salary, item.currency)}</b></li>)}</ul>
          </div>
        )}
      </div>
    </section>
  );
}

const stages = [
  { number: "01", title: "Foundation", text: "Build your direction and plan.", checks: ["Define your goals", "Explore career paths", "Create your study plan"], tone: "dark" },
  { number: "02", title: "Core skills", text: "Learn the skills that matter.", checks: ["Complete key courses", "Build practical skills", "Pass skill assessments"], tone: "dark" },
  { number: "03", title: "Portfolio", text: "Turn your learning into real work.", checks: ["Complete 3 projects", "Get feedback", "Polish your portfolio"], tone: "lime" },
  { number: "04", title: "Internship", text: "Gain real-world experience.", checks: ["Apply to roles", "Complete interviews", "Start your internship"], tone: "light" },
  { number: "05", title: "First job", text: "Land offers and start your career.", checks: ["Apply to full-time roles", "Receive your offer", "Start your first job"], tone: "light" },
] as const;

export function CareerRoadmap() {
  const [active, setActive] = useState(2);
  const { data } = useLandingData();
  const [target, setTarget] = useState("Python Backend Developer");
  const careers = data?.careers ?? [];
  const roles = Array.from(new Set(careers.map((item) => item.career_target)));
  const medians = careers.filter((item) => item.career_target === target);
  const moveStage = (direction: number) => setActive((current) => Math.min(stages.length - 1, Math.max(0, current + direction)));
  const journeyRef = useCarouselGestures<HTMLDivElement>(moveStage, ".roadmap-journey");
  useEffect(() => {
    const journey = journeyRef.current;
    const step = journey?.querySelector<HTMLElement>(`[data-roadmap-index="${active}"]`);
    if (!journey || !step || journey.scrollWidth <= journey.clientWidth + 1) return;
    journey.scrollTo({ left: Math.max(0, step.offsetLeft - (journey.clientWidth - step.offsetWidth) / 2), behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  }, [active, journeyRef]);
  const current = stages[active];
  return (
    <section className="feature-section roadmap-section motion-section" id="roadmap" data-motion-section="true" data-header-theme="light" aria-labelledby="roadmap-title">
      <div className="feature-shell roadmap-shell">
        <div className="roadmap-top"><div className="feature-intro"><p className="feature-label"><i /> 05 / CAREER ROADMAP PREVIEW</p><h2 id="roadmap-title"><HeadlineLine>From <span className="oval-highlight">choice</span> to</HeadlineLine><HeadlineLine><span className="rect-highlight lime-marker">job readiness.</span></HeadlineLine></h2><p className="feature-description">Pick a target role and get the steps in order: skills to learn, projects to ship, applications to send. Tick them off as you go.</p></div><div className="roadmap-metrics"><b>5 <span>stages<small>from direction to role</small></span></b><b>24 <span>example skills<small>to validate by target role</small></span></b><b>6 <span>project ideas<small>for a credible portfolio</small></span></b></div>
          <aside className="roadmap-target">
            <label><span>Your target</span>
              <select value={target} onChange={(event) => setTarget(event.target.value)}>{(roles.length ? roles : [target]).map((item) => <option key={item}>{item}</option>)}</select>
            </label>
            {medians.length > 0 && <p>Median {medians.map((item) => formatMoney(item.median_salary, item.currency)).join(" · ")} a year</p>}
            <strong>Now: {current.title}</strong>
            <ul>{current.checks.map((check, index) => <li key={check} className={index === 0 ? "done" : ""}>{check}</li>)}</ul>
            <Link className="live-link" href="/register">Build this roadmap <Arrow /></Link>
          </aside>
        </div>
        <div className="roadmap-journey" aria-label="Five stage career roadmap" ref={journeyRef}>{stages.map((stage, index) => {
          const state = index < active ? "done" : index === active ? "current" : "next";
          const progress = state === "done" ? 100 : state === "current" ? 33 : 0;
          return (
            <div className="roadmap-step" data-state={state} data-roadmap-index={index} key={stage.number}>
              <button type="button" className="roadmap-node" aria-label={`Go to stage ${index + 1}: ${stage.title}`} aria-current={index === active ? "step" : undefined} onClick={() => setActive(index)}>{state === "done" ? <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m5 13 4 4L19 7" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" /></svg> : <span>{index + 1}</span>}</button>
              <button type="button" className={`roadmap-card roadmap-card--${stage.tone} ${index === active ? "is-current" : ""}`} onClick={() => setActive(index)}><span className="roadmap-number">{stage.number}</span>{index === active && <span className="you-are">You are here</span>}<h3>{stage.title}</h3><p>{stage.text}</p><ul>{stage.checks.map((check, checkIndex) => <li className={state === "done" || (state === "current" && checkIndex === 0) ? "done" : ""} key={check}>{check}</li>)}</ul><footer><span>Progress</span><b>{progress}%</b><i><em style={{ width: `${progress}%` }} /></i></footer></button>
            </div>
          );
        })}</div>
      </div>
    </section>
  );
}

const scholarships = [
  { title: "Future Builders Grant", copy: "Sample funding scenario for undergraduate STEM study.", amount: "$8,000", deadline: "Preview only", country: "United States", match: 92, tags: ["Undergraduate", "STEM"], tone: "light", symbol: "grant" },
  { title: "EU Digital Talent", copy: "Sample funding scenario for digital study in Europe.", amount: "\u20AC6,500", deadline: "Preview only", country: "European Union", match: 87, tags: ["Bachelor's", "Digital Skills"], tone: "dark", symbol: "digital" },
  { title: "Women in Data Fund", copy: "Sample funding scenario for data and AI education.", amount: "$5,000", deadline: "Preview only", country: "Global", match: 81, tags: ["Women in Tech", "Data & AI"], tone: "lime", symbol: "women" },
  { title: "Local Innovation Award", copy: "Sample funding scenario for community-focused projects.", amount: "\u20AC3,000", deadline: "Preview only", country: "Selected regions", match: 76, tags: ["Any level", "Social Impact"], tone: "light", symbol: "local" },
] as const;

export function Scholarships() {
  const [active, setActive] = useState(0);
  const carouselRef = useRef<HTMLDivElement>(null);
  const scrollFrameRef = useRef<number | null>(null);
  const scrollReleaseRef = useRef<number | null>(null);
  const programmaticScrollRef = useRef(false);
  const selectCard = (index: number) => {
    setActive(index);
    if (!window.matchMedia("(max-width: 700px)").matches) return;
    programmaticScrollRef.current = true;
    const carousel = carouselRef.current;
    const card = carousel?.querySelector<HTMLElement>(`[data-scholarship-index="${index}"]`);
    if (carousel && card) carousel.scrollTo({ left: card.offsetLeft - (carousel.clientWidth - card.offsetWidth) / 2, behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    if (scrollReleaseRef.current !== null) window.clearTimeout(scrollReleaseRef.current);
    scrollReleaseRef.current = window.setTimeout(() => {
      programmaticScrollRef.current = false;
      scrollReleaseRef.current = null;
    }, 1400);
  };
  const move = (direction: number) => selectCard((active + direction + scholarships.length) % scholarships.length);
  const shellRef = useCarouselGestures<HTMLDivElement>(move, ".scholarship-carousel");
  const grant = useLandingData().data?.grant_example;
  const syncActiveToScroll = () => {
    if (programmaticScrollRef.current || scrollFrameRef.current !== null) return;
    scrollFrameRef.current = window.requestAnimationFrame(() => {
      scrollFrameRef.current = null;
      const carousel = carouselRef.current;
      if (!carousel || carousel.clientWidth >= carousel.scrollWidth) return;
      const center = carousel.scrollLeft + carousel.clientWidth / 2;
      const nextIndex = scholarships.reduce((best, _, index) => {
        const card = carousel.querySelector<HTMLElement>(`[data-scholarship-index="${index}"]`);
        const current = carousel.querySelector<HTMLElement>(`[data-scholarship-index="${best}"]`);
        if (!card || !current) return best;
        const cardCenter = card.offsetLeft + card.offsetWidth / 2;
        const bestCenter = current.offsetLeft + current.offsetWidth / 2;
        return Math.abs(cardCenter - center) < Math.abs(bestCenter - center) ? index : best;
      }, active);
      setActive((current) => current === nextIndex ? current : nextIndex);
    });
  };
  useEffect(() => () => {
    if (scrollFrameRef.current !== null) window.cancelAnimationFrame(scrollFrameRef.current);
    if (scrollReleaseRef.current !== null) window.clearTimeout(scrollReleaseRef.current);
  }, []);
  const handleCardKeyDown = (event: KeyboardEvent<HTMLElement>, index: number) => {
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); selectCard(index); }
  };
  return (
    <section className="feature-section scholarships-section motion-section" id="scholarships" data-motion-section="true" data-header-theme="light" aria-labelledby="scholarships-title">
      <div className="scholarship-crest"><span>06 / Funding scenarios</span><i /><span>Lower cost. Stronger options.</span></div>
      <div className="feature-shell scholarship-shell" ref={shellRef}><div className="scholarships-head"><div className="feature-intro"><h2 id="scholarships-title"><HeadlineLine><span className="oval-highlight">Funding</span></HeadlineLine><HeadlineLine>changes the</HeadlineLine><HeadlineLine>whole <span className="rect-highlight lime-marker">decision.</span></HeadlineLine></h2></div><p className="feature-description">A grant can cut payback by years. Add funding to any scenario and Fence recalculates total cost and payback at once. The cards below are examples.</p><a className="dark-pill-button" href="/register">Add funding to a scenario <Arrow /></a></div>
        <div className="scholarship-carousel" data-active={active} ref={carouselRef} onScroll={syncActiveToScroll}>{scholarships.map((item, index) => <article className={`scholarship-card scholarship-card--${item.tone} ${active === index ? "is-active" : ""}`} key={item.title} data-scholarship-index={index} role="button" tabIndex={0} aria-label={`Select ${item.title}`} aria-pressed={active === index} onClick={() => selectCard(index)} onKeyDown={(event) => handleCardKeyDown(event, index)}><span className="scholarship-symbol" aria-hidden="true"><SymbolIcon kind={item.symbol} /></span><h3>{item.title}</h3><p>{item.copy}</p><div className="scholarship-rule" /><div className="scholarship-amount"><span>Amount</span><strong>{item.amount}</strong></div><div className="match-ring" style={{ "--match": `${item.match * 3.6}deg` } as CSSProperties}><b>{item.match}%<small>Match</small></b></div><div className="scholarship-meta" id={`scholarship-${index}`}><span><b>Deadline</b>{item.deadline}</span><span><b>Country</b>{item.country}</span></div><div className="scholarship-tags">{item.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>{item.title === "Local Innovation Award" && <i className="blur-orb scholarship-orb" aria-hidden="true" />}</article>)}</div>
        <div className="carousel-controls scholarship-controls" role="group" aria-label="Scholarship controls"><button type="button" aria-label="Show previous scholarship" onClick={() => move(-1)}><Arrow direction="left" /></button><output aria-live="polite">{String(active + 1).padStart(2, "0")} / 04</output><button type="button" aria-label="Show next scholarship" onClick={() => move(1)}><Arrow /></button></div>
        {grant && (
          <div className="grant-live">
            <div><h3>A {formatMoney(grant.grant, grant.without_grant.currency)} grant on a {formatMoney(grant.without_grant.annual_tuition, grant.without_grant.currency)} a year programme</h3><p>{grant.label}. Calculated by the same engine, not an estimate on this page.</p></div>
            <dl><div><dt>Payback</dt><dd>{grant.without_grant.payback_months ?? "120+"} → {grant.with_grant.payback_months ?? "120+"} months</dd></div><div><dt>10-year ROI</dt><dd>{formatRoi(grant.without_grant.roi_percent)} → {formatRoi(grant.with_grant.roi_percent)}</dd></div></dl>
          </div>
        )}
      </div>
      <p className="sr-only" aria-live="polite">Viewing {scholarships[active].title} scholarship.</p>
    </section>
  );
}

export function FinalDecision() {
  const routes = [
    { number: "01", title: "Compare education paths", copy: "Review costs and outcome assumptions side by side before narrowing the shortlist.", tone: "dark", foot: "Compare in your workspace", href: "/register" },
    { number: "02", title: "Model cost and payback", copy: "Turn tuition, scholarships, study time, and salary assumptions into a scenario.", tone: "light", foot: "Try it without an account", href: "/try" },
    { number: "03", title: "Plan career readiness", copy: "Connect a target role to the skills, projects, and experience still needed.", tone: "lime", foot: "Plan in your workspace", href: "/register" },
  ];
  const { data, scenario } = useLandingData();
  const [focus, setFocus] = useState<"Poland" | "Ukraine" | undefined>(undefined);
  const careers = data?.careers ?? [];
  const inFocus = focus ? careers.filter((item) => item.country === focus) : careers;
  const roleCount = new Set(inFocus.map((item) => item.career_target)).size;
  const countryCount = new Set(inFocus.map((item) => item.country)).size;
  const knu = scenario("knu-python");
  const warsaw = scenario("warsaw-python");
  return <section className="feature-section final-decision-section dark-feature motion-section" id="final-decision" data-motion-section="true" data-header-theme="dark" aria-labelledby="final-decision-title"><div className="feature-shell final-shell"><div className="final-head"><p className="feature-label">08 / ONE CONNECTED DECISION</p><h2 id="final-decision-title"><HeadlineLine>Your future should</HeadlineLine><HeadlineLine><span className="oval-highlight">not</span> be a <span className="rect-highlight lime-marker">guess.</span></HeadlineLine></h2><p>Compare the paths, check the money, then close the gaps that matter. One scenario is enough to see the difference.</p><a className="forecast-cta" href="/register">Create my first scenario <span><Arrow /></span></a></div>
    {careers.length > 0 && (
      <div className="final-data">
        <article className="final-map">
          <header><div><h3>Poland and Ukraine</h3><p>Both markets, in local currency.</p></div>
            <div className="live-toggle" role="group" aria-label="Focus on a country">{(["Poland", "Ukraine"] as const).map((item) => <button type="button" key={item} aria-pressed={focus === item} onClick={() => setFocus((current) => (current === item ? undefined : item))}>{item}</button>)}</div>
          </header>
          <CoverageMap labels focus={focus} />
        </article>
        <article className="final-numbers">
          <h3>Behind every number</h3>
          <div className="final-counts"><div><b>{roleCount}</b><small>careers</small></div><div><b>{inFocus.length}</b><small>salary snapshots</small></div><div><b>{countryCount}</b><small>{countryCount === 1 ? "country" : "countries"}</small></div></div>
          <dl><div><dt>Salaries</dt><dd>Pracuj.pl, No Fluff Jobs, DOU</dd></div><div><dt>State register</dt><dd>Employment Service of Ukraine</dd></div><div><dt>Official statistics</dt><dd>Eurostat, World Bank</dd></div><div><dt>Exchange rates</dt><dd>NBP, NBU</dd></div></dl>
        </article>
      </div>
    )}
    <div className="decision-branches" aria-hidden="true"><i /><i /><i /></div><div className="decision-routes">{routes.map((route) => <Link className={`decision-route decision-route--${route.tone}`} href={route.href} key={route.number}><span>{route.number}</span><i aria-hidden="true"><Arrow /></i><h3>{route.title}</h3><p>{route.copy}</p><small>{route.foot}</small></Link>)}</div>
    <div className="final-proof">
      {knu && warsaw && (
        <article className="final-payback"><h3>Payback, Python backend</h3>
          {[{ name: "KNU Kyiv", result: knu, tone: "lime" }, { name: "Warsaw Tech", result: warsaw, tone: "violet" }].map((row) => <div key={row.name}><span>{row.name}</span><i className={`is-${row.tone}`}><em style={{ width: `${paybackShare(row.result.payback_months)}%` }} /></i><b>{formatYears(row.result.payback_months)}</b></div>)}
        </article>
      )}
      <article className="final-deterministic"><h3>Same inputs, same result</h3><p>Every saved calculation keeps its sources and method version, so you can always see where a number came from.</p></article>
    </div>
  </div></section>;
}
