import { useEffect, useRef, useState, type CSSProperties, type KeyboardEvent, type PointerEvent, type WheelEvent } from "react";
import Image from "next/image";
import { HeadlineLine } from "../hooks/useScrollMotion";
import { createScreenProjection, type ScreenPoint } from "../utils/screenProjection";
import { useScaledFrame } from "../hooks/useScaledFrame";

function Arrow({ direction = "right" }: { direction?: "left" | "right" }) {
  const right = direction === "right";
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" focusable="false">
      <path d={right ? "M5 12h14m-6-6 6 6-6 6" : "M19 12H5m6 6-6-6 6-6"} stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function useSwipe(move: (direction: number) => void) {
  const start = useRef<number | null>(null);
  return {
    onPointerDown: (event: PointerEvent<HTMLElement>) => {
      if (event.pointerType === "touch") start.current = event.clientX;
    },
    onPointerUp: (event: PointerEvent<HTMLElement>) => {
      if (event.pointerType !== "touch" || start.current === null) return;
      const offset = event.clientX - start.current;
      start.current = null;
      const scrollTarget = event.currentTarget.matches(".scholarship-carousel, .university-cards")
        ? event.currentTarget
        : event.currentTarget.querySelector<HTMLElement>(".university-cards, .scholarship-carousel");
      if (scrollTarget && scrollTarget.scrollWidth > scrollTarget.clientWidth) return;
      if (Math.abs(offset) > 38) move(offset > 0 ? -1 : 1);
    },
    onWheel: (event: WheelEvent<HTMLElement>) => {
      if (Math.abs(event.deltaX) <= Math.abs(event.deltaY) || event.deltaX === 0) return;
      const scrollTarget = event.currentTarget.matches(".scholarship-carousel, .university-cards")
        ? event.currentTarget
        : event.currentTarget.querySelector<HTMLElement>(".university-cards, .scholarship-carousel");
      if (!scrollTarget || scrollTarget.scrollWidth <= scrollTarget.clientWidth) return;
      event.preventDefault();
      const multiplier = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? window.innerWidth : 1;
      scrollTarget.scrollLeft += event.deltaX * multiplier;
    },
  };
}

const universities = [
  { name: "US Research University", strap: "High investment. Higher salary assumption.", tuition: 45000, employment: 91, salary: 112000, scholarship: 15000, currency: "USD", icon: "campus", tone: "dark", best: false },
  { name: "Canadian Public University", strap: "Balanced cost and outcome scenario.", tuition: 39000, employment: 89, salary: 96000, scholarship: 12000, currency: "USD", icon: "globe", tone: "light", best: true },
  { name: "European City University", strap: "Lower tuition. Different market context.", tuition: 17000, employment: 88, salary: 74000, scholarship: 8000, currency: "EUR", icon: "spark", tone: "lime", best: false },
] as const;

function money(amount: number, currency: string) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency, maximumFractionDigits: 0 }).format(amount);
}

function compactMoney(amount: number, currency: string) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency, notation: "compact", maximumFractionDigits: 0 }).format(amount);
}

function forecast(tuition: number, scholarship: number, years: number, salary: number, employment: number) {
  const investment = Math.max(0, (tuition - scholarship) * years);
  let annual = salary;
  let earnings = 0;
  let paybackMonths = investment === 0 ? 0 : 120;
  let cumulative = 0;
  for (let year = 1; year <= 10; year += 1) {
    if (year > 1) annual *= year <= 3 ? 1.08 : year <= 6 ? 1.05 : 1.03;
    const expectedAnnual = annual * employment / 100;
    earnings += expectedAnnual;
    if (cumulative < investment && cumulative + expectedAnnual >= investment) {
      paybackMonths = Math.ceil((year - 1 + (investment - cumulative) / expectedAnnual) * 12);
    }
    cumulative += expectedAnnual;
  }
  return { investment, earnings, roi: investment === 0 ? null : Math.round((earnings - investment) / investment * 100), paybackMonths };
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
  const [tuition, setTuition] = useState(45000);
  const [years, setYears] = useState(4);
  const [university, setUniversity] = useState("US Research University");
  const [career, setCareer] = useState("Software Engineer");
  const [hasCalculated, setHasCalculated] = useState(false);
  const { frameRef: calculatorFrameRef, scale: calculatorScale } = useScaledFrame<HTMLDivElement>(920);

  const selectedUniversity = universities.find((item) => item.name === university) ?? universities[0];
  const careerMultiplier = career === "Data Analyst" ? .78 : career === "UX Designer" ? .86 : 1;
  const annualSalary = Math.round(selectedUniversity.salary * careerMultiplier);
  const result = forecast(tuition, selectedUniversity.scholarship, years, annualSalary, selectedUniversity.employment);
  const chooseUniversity = (name: string) => {
    const selected = universities.find((item) => item.name === name);
    if (!selected) return;
    setUniversity(name);
    setTuition(selected.tuition);
    setHasCalculated(false);
  };
  const screenProjection = createScreenProjection(defaultScreenCorners, 600, 440);

  return (
    <section className="feature-section calculator-section motion-section" id="calculator" data-motion-section="true" data-header-theme="light" aria-labelledby="calculator-title">
      <div className="feature-shell calculator-shell">
        <div className="feature-intro calculator-intro">
          <p className="feature-label"><i /> 02 / LIVE FORECAST</p>
          <h2 id="calculator-title"><HeadlineLine>Test the <span className="oval-highlight">value</span> before</HeadlineLine><HeadlineLine>you <span className="rect-highlight lime-marker">commit.</span></HeadlineLine></h2>
          <p className="feature-description">Education is an investment. Adjust an illustrative university and career scenario to see how tuition, scholarships and salary affect the return.</p>
        </div>
        
        <div className="calculator-device-viewport">
          <div ref={calculatorFrameRef} className="calculator-device-frame" style={{ "--calculator-scale": calculatorScale } as CSSProperties}>
            <div className="calculator-board ipad-device" aria-label="Interactive education ROI calculator" style={{ "--calculator-screen-transform": screenProjection } as CSSProperties}>
              <Image className="calculator-device-art" src="/fence-ipad-keyboard.webp" alt="Floating iPad with keyboard displaying the education ROI calculator" width={1254} height={1254} quality={85} priority sizes="(max-width: 720px) 100vw, (max-width: 1180px) 92vw, 920px" />

              <aside className="calculator-rail" aria-hidden="true"><b>F</b><span> ROI calculator</span><span> Career paths</span><span> Compare</span><span> Saved scenarios</span></aside>
              <div className="calculator-main">
                <header><div><h3>Education ROI Calculator</h3><p>Estimate the return from your education investment.</p></div><span className="calculator-breadcrumb">Education / Outcomes / You</span></header>
                <div className="calculator-form">
                  <label className="calculator-field calculator-field--select">University<div className="calculator-select-wrap"><select value={university} onChange={(event) => chooseUniversity(event.target.value)}>{universities.map((item) => <option key={item.name}>{item.name}</option>)}</select></div></label>
                  <label className="calculator-field calculator-field--range">Annual tuition ({selectedUniversity.currency})<output>{money(tuition, selectedUniversity.currency)}</output><input type="range" min="5000" max="50000" step="1000" value={tuition} style={{ "--range-progress": `${((tuition - 5000) / 45000) * 100}%` } as CSSProperties} onChange={(event) => setTuition(Number(event.target.value))} /></label>
                  <label className="calculator-field calculator-field--range">Study length <output>{years} years</output><input type="range" min="1" max="6" value={years} style={{ "--range-progress": `${((years - 1) / 5) * 100}%` } as CSSProperties} onChange={(event) => setYears(Number(event.target.value))} /></label>
                  <label className="calculator-field calculator-field--select">Career goal<div className="calculator-select-wrap"><select value={career} onChange={(event) => setCareer(event.target.value)}><option>Software Engineer</option><option>Data Analyst</option><option>UX Designer</option></select></div></label>
                  <button type="button" className="calculate-button" onClick={() => setHasCalculated(true)}> Calculate ROI <Arrow /></button>
                </div>
                <div className="calculator-results" aria-live="polite">
                  <article className="roi-result"><span>Estimated 10-year ROI</span><strong>{result.roi === null ? "N/A" : `${result.roi.toLocaleString()}%`} <i></i></strong><small>{result.investment === 0 ? "Scholarship covers tuition" : hasCalculated ? `Calculated for ${university}` : `Net tuition ${money(result.investment, selectedUniversity.currency)}`}</small></article>
                  <article className="payback-result"><span>Payback Period</span><strong>{result.paybackMonths} months</strong><small>{result.investment === 0 ? "No net tuition to recover" : "Expected earnings cover net tuition"}</small><i className="blur-orb" aria-hidden="true" /></article>
                  <article className="salary-result"><span>Estimated Starting Salary</span><strong>{compactMoney(annualSalary, selectedUniversity.currency)}</strong><small>{money(annualSalary, selectedUniversity.currency)} / year for {career}</small><b aria-hidden="true"></b></article>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export function UniversityComparison() {
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
      selectUniversity(Math.min(active + 1, universities.length - 1));
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
      const next = universities.reduce((closest, _, index) => {
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

  return (
    <section className="feature-section comparison-section dark-feature motion-section" id="comparison" data-motion-section="true" data-header-theme="dark" aria-labelledby="comparison-title" tabIndex={0} onKeyDown={onKeyDown}>
      <div className="feature-shell comparison-shell">
        <div className="feature-intro dark-intro">
          <p className="feature-label">03 / EDUCATION PATH COMPARISON</p>
          <h2 id="comparison-title"><HeadlineLine>Compare <span className="oval-highlight">more</span> than</HeadlineLine><HeadlineLine><span className="rect-highlight violet-marker">rankings.</span></HeadlineLine></h2>
          <p className="feature-description">Compare sample paths side by side to see how tuition, funding, employment, and salary assumptions change the result.</p>
          <div className="comparison-count"><strong>03</strong><span>Options</span><i /></div>
        </div>
        <div className="comparison-area">
          <div className="university-cards" data-active={active} ref={cardsRef} onScroll={syncActiveToScroll}>
            {universities.map((university, index) => {
              const result = forecast(university.tuition, university.scholarship, 4, university.salary, university.employment);
              return (
              <article className={`university-card university-card--${university.tone} ${active === index ? "is-active" : ""}`} key={university.name} aria-label={`${university.name}, ${active === index ? "selected" : "option"}`} data-university-index={index}>
                <button className="university-card-select" type="button" aria-label={`Select ${university.name}`} aria-pressed={active === index} onClick={() => selectUniversity(index)} />
                <span className="university-icon" aria-hidden="true"><SymbolIcon kind={university.icon} /></span>
                {university.best && <span className="best-fit"><i aria-hidden="true"><SymbolIcon kind="spark" /></i> Featured</span>}
                <h3>{university.name}</h3><p>{university.strap}</p>
                <dl id={`university-${index}`}><div><dt>Annual Tuition</dt><dd>{money(university.tuition, university.currency)}</dd></div><div><dt>Employment Rate</dt><dd>{university.employment}%</dd></div><div><dt>Starting Salary</dt><dd>{money(university.salary, university.currency)}</dd></div><div><dt>Annual Scholarship</dt><dd>{money(university.scholarship, university.currency)}</dd></div></dl>
                <div className="university-score"><span>Estimated 10-year ROI</span><strong>{result.roi === null ? "N/A" : `${result.roi.toLocaleString()}%`}</strong><span>Net 4-year tuition <b>{money(result.investment, university.currency)}</b></span><i><em style={{ width: `${university.employment}%` }} /></i><small>{university.employment}% employment assumption</small></div>
              </article>
              );
            })}
          </div>
          <p className="comparison-method">Illustrative estimates: 4 years of tuition after annual scholarship, 10 years of salary with 8% / 5% / 3% growth, weighted by the shown employment rate. Before tax and living costs.</p>
        </div>
      </div>
      <p className="sr-only" aria-live="polite">Viewing {universities[active].name}.</p>
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
  return (
    <section className="feature-section factors-section dark-feature motion-section" id="factors" data-motion-section="true" data-header-theme="dark" aria-labelledby="factors-title">
      <div className="feature-shell factors-shell">
        <div className="feature-intro dark-intro factors-intro"><p className="feature-label"><i /> 04 / WHAT SHAPES THE OUTCOME</p><h2 id="factors-title"><HeadlineLine>Your outcome</HeadlineLine><HeadlineLine>is shaped by</HeadlineLine><HeadlineLine><span className="oval-highlight">more</span> than</HeadlineLine><HeadlineLine>a degree.</HeadlineLine></h2><p className="feature-description">Test how location, experience, internships, and market demand can change a career scenario. Every figure shown here is illustrative, not a promise.</p><button type="button" className="lime-button inactive-cta" disabled aria-disabled="true">Path builder coming soon <span><Arrow /></span></button><div className="factor-proof"><b>6<small>decision factors</small></b><b>Scenario-based<small>salary assumptions</small></b><b>One view<small>of the trade-offs</small></b></div></div>
        <div className="factor-orbit" aria-label="Interactive career outcome factors">
          <div className="orbit-circle orbit-circle--outer" aria-hidden="true" /><div className="orbit-circle orbit-circle--middle" aria-hidden="true" /><div className="orbit-circle orbit-circle--inner" aria-hidden="true" />
          <div className="salary-core" aria-live="polite"><span>Projected salary</span><strong>{factor.salary}</strong><small>Illustrative US data analyst benchmark</small></div>
          {factors.map((item, index) => <button className={`factor-card factor-card--${index} ${selected === index ? "is-selected" : ""}`} type="button" key={item.name} aria-pressed={selected === index} onClick={() => setSelected(index)}><i aria-hidden="true"><SymbolIcon kind={item.icon} /></i><span><b>{item.name}</b><small>{item.detail}</small></span><strong>{item.delta}</strong></button>)}
        </div>
      </div>
    </section>
  );
}

const stages = [
  { number: "01", title: "Foundation", text: "Build your direction and plan.", checks: ["Define your goals", "Explore career paths", "Create your study plan"], progress: 100, tone: "dark" },
  { number: "02", title: "Core skills", text: "Learn the skills that matter.", checks: ["Complete key courses", "Build practical skills", "Pass skill assessments"], progress: 67, tone: "dark" },
  { number: "03", title: "Portfolio", text: "Turn your learning into real work.", checks: ["Complete 3 projects", "Get feedback", "Polish your portfolio"], progress: 33, tone: "lime" },
  { number: "04", title: "Internship", text: "Gain real-world experience.", checks: ["Apply to roles", "Complete interviews", "Start your internship"], progress: 0, tone: "light" },
  { number: "05", title: "First job", text: "Land offers and start your career.", checks: ["Apply to full-time roles", "Receive your offer", "Start your first job"], progress: 0, tone: "light" },
] as const;

export function CareerRoadmap() {
  const [active, setActive] = useState(0);
  const journeyRef = useRef<HTMLDivElement>(null);
  const progress = (active + 1) * 20;
  useEffect(() => {
    if (!window.matchMedia("(max-width: 700px)").matches) return;
    const journey = journeyRef.current;
    const card = journey?.querySelector<HTMLElement>(`[data-roadmap-index="${active}"]`);
    if (!journey || !card || journey.scrollWidth <= journey.clientWidth) return;
    const targetLeft = card.offsetLeft - (journey.clientWidth - card.offsetWidth) / 2;
    journey.scrollTo({ left: Math.max(0, targetLeft), behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  }, [active]);
  return (
    <section className="feature-section roadmap-section motion-section" id="roadmap" data-motion-section="true" data-header-theme="light" aria-labelledby="roadmap-title">
      <div className="feature-shell roadmap-shell">
        <div className="roadmap-top"><div className="feature-intro"><p className="feature-label"><i /> 05 / CAREER ROADMAP PREVIEW</p><h2 id="roadmap-title"><HeadlineLine>From <span className="oval-highlight">choice</span> to</HeadlineLine><HeadlineLine><span className="rect-highlight lime-marker">job readiness.</span></HeadlineLine></h2><p className="feature-description">Turn a career target into a practical sequence of skills, projects, applications, and experience.</p></div><div className="roadmap-metrics"><b>5 <span>stages<small>from direction to role</small></span></b><b>24 <span>example skills<small>to validate by target role</small></span></b><b>6 <span>project ideas<small>for a credible portfolio</small></span></b></div></div>
        <div className="roadmap-journey" aria-label="Five stage career roadmap" ref={journeyRef}><div className="roadmap-line" aria-hidden="true"><svg viewBox="0 0 1000 160" preserveAspectRatio="none"><path className="roadmap-line-base" pathLength="100" d="M0 133C78 133 102 87 200 87S306 52 400 52s109-45 200-45 116 45 200 45 118-22 200-22" /><path className="roadmap-line-progress" pathLength="100" style={{ strokeDashoffset: 100 - progress }} d="M0 133C78 133 102 87 200 87S306 52 400 52s109-45 200-45 116 45 200 45 118-22 200-22" /><circle cx="0" cy="133" r="11" /><circle cx="200" cy="87" r="11" /><circle cx="400" cy="52" r="12" /><circle cx="600" cy="7" r="11" /><circle cx="800" cy="52" r="11" /><circle cx="1000" cy="30" r="11" /></svg></div>{stages.map((stage, index) => <button type="button" className={`roadmap-card roadmap-card--${stage.tone} ${active === index ? "is-current" : ""}`} onClick={() => setActive(index)} aria-current={active === index ? "step" : undefined} data-roadmap-index={index} key={stage.number}><span className="roadmap-number">{stage.number}</span>{active === index && <span className="you-are">You are here</span>}<h3>{stage.title}</h3><p>{stage.text}</p><ul>{stage.checks.map((check, checkIndex) => <li className={checkIndex < Math.max(1, 3 - index) ? "done" : ""} key={check}>{check}</li>)}</ul><footer><span>Progress</span><b>{stage.progress}%</b><i><em style={{ width: `${stage.progress}%` }} /></i></footer></button>)}</div>
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
  const swipe = useSwipe(move);
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
      <div className="feature-shell scholarship-shell"><div className="scholarships-head"><div className="feature-intro"><h2 id="scholarships-title"><HeadlineLine><span className="oval-highlight">Funding</span></HeadlineLine><HeadlineLine>changes the</HeadlineLine><HeadlineLine>whole <span className="rect-highlight lime-marker">decision.</span></HeadlineLine></h2></div><p className="feature-description">See how grants and scholarships could change total investment and payback. Listings below are interface examples until verified sources are connected.</p><button className="dark-pill-button inactive-cta" type="button" disabled aria-disabled="true">Matching coming soon <Arrow /></button></div>
        <div className="scholarship-carousel" data-active={active} ref={carouselRef} onScroll={syncActiveToScroll} {...swipe}>{scholarships.map((item, index) => <article className={`scholarship-card scholarship-card--${item.tone} ${active === index ? "is-active" : ""}`} key={item.title} data-scholarship-index={index} role="button" tabIndex={0} aria-label={`Select ${item.title}`} aria-pressed={active === index} onClick={() => selectCard(index)} onKeyDown={(event) => handleCardKeyDown(event, index)}><span className="scholarship-symbol" aria-hidden="true"><SymbolIcon kind={item.symbol} /></span><h3>{item.title}</h3><p>{item.copy}</p><div className="scholarship-rule" /><div className="scholarship-amount"><span>Amount</span><strong>{item.amount}</strong></div><div className="match-ring" style={{ "--match": `${item.match * 3.6}deg` } as CSSProperties}><b>{item.match}%<small>Match</small></b></div><div className="scholarship-meta" id={`scholarship-${index}`}><span><b>Deadline</b>{item.deadline}</span><span><b>Country</b>{item.country}</span></div><div className="scholarship-tags">{item.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>{item.title === "Local Innovation Award" && <i className="blur-orb scholarship-orb" aria-hidden="true" />}</article>)}</div>
        <div className="carousel-controls scholarship-controls" role="group" aria-label="Scholarship controls"><button type="button" aria-label="Show previous scholarship" onClick={() => move(-1)}><Arrow direction="left" /></button><output aria-live="polite">{String(active + 1).padStart(2, "0")} / 04</output><button type="button" aria-label="Show next scholarship" onClick={() => move(1)}><Arrow /></button></div>
      </div>
      <p className="sr-only" aria-live="polite">Viewing {scholarships[active].title} scholarship.</p>
    </section>
  );
}

export function FinalDecision() {
  const routes = [
    { number: "01", title: "Compare education paths", copy: "Review costs and outcome assumptions side by side before narrowing the shortlist.", tone: "dark", foot: "Comparison preview" },
    { number: "02", title: "Model cost and payback", copy: "Turn tuition, scholarships, study time, and salary assumptions into a scenario.", tone: "light", foot: "Deterministic calculation" },
    { number: "03", title: "Plan career readiness", copy: "Connect a target role to the skills, projects, and experience still needed.", tone: "lime", foot: "Roadmap preview" },
  ];
  return <section className="feature-section final-decision-section dark-feature motion-section" id="final-decision" data-motion-section="true" data-header-theme="dark" aria-labelledby="final-decision-title"><div className="feature-shell final-shell"><div className="final-head"><p className="feature-label">08 / ONE CONNECTED DECISION</p><h2 id="final-decision-title"><HeadlineLine>Your future should</HeadlineLine><HeadlineLine><span className="oval-highlight">not</span> be a <span className="rect-highlight lime-marker">guess.</span></HeadlineLine></h2><p>Compare the path, test the financial assumptions, then act on the gaps that matter.</p><button type="button" className="forecast-cta inactive-cta" disabled aria-disabled="true">Personal forecasts coming soon <span><Arrow /></span></button></div><div className="decision-branches" aria-hidden="true"><i /><i /><i /></div><div className="decision-routes">{routes.map((route) => <article className={`decision-route decision-route--${route.tone}`} aria-disabled="true" key={route.number}><span>{route.number}</span><i aria-hidden="true"><Arrow /></i><h3>{route.title}</h3><p>{route.copy}</p><small>{route.foot}</small></article>)}</div></div></section>;
}
