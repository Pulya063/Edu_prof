import { useEffect, useRef, useState, type CSSProperties, type KeyboardEvent, type PointerEvent, type WheelEvent } from "react";
import Image from "next/image";
import { HeadlineLine } from "./motion";
import { createScreenProjection, type ScreenPoint } from "./screenProjection";
import { useScaledFrame } from "./useScaledFrame";

type Navigate = (target: string) => void;

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
  { name: "University of California, Berkeley", strap: "Research-led. Future-focused.", tuition: "$45,000", employment: "91%", salary: "$112,000", scholarship: "$15,000", roi: "149%", fit: 88, icon: "⌂", tone: "dark", best: false },
  { name: "University of Toronto", strap: "Practical skills. Global reach.", tuition: "$39,000", employment: "89%", salary: "$96,000", scholarship: "$12,000", roi: "166%", fit: 92, icon: "⌁", tone: "light", best: true },
  { name: "University of Amsterdam", strap: "Open minds. Strong outcomes.", tuition: "€17,000", employment: "88%", salary: "€74,000", scholarship: "€8,000", roi: "238%", fit: 86, icon: "✦", tone: "lime", best: false },
] as const;

const defaultScreenCorners = [
  // Extend slightly beneath the bezel so no green edge remains visible.
  { x: 61.5, y: 277 },
  { x: 496.2, y: 105.1 },
  { x: 646.2, y: 428 },
  { x: 216.7, y: 630.7 },
] as const;

export function LiveRoiCalculator() {
  const [tuition, setTuition] = useState(28000);
  const [years, setYears] = useState(4);
  const [university, setUniversity] = useState("University of California, Berkeley");
  const [career, setCareer] = useState("Software Engineer");
  const [hasCalculated, setHasCalculated] = useState(false);
  const { frameRef: calculatorFrameRef, scale: calculatorScale } = useScaledFrame<HTMLDivElement>(920);

  const annualSalary = career === "Data Analyst" ? 68000 : career === "UX Designer" ? 76000 : 92000;
  const totalTuition = tuition * years;
  const tenYearEarnings = annualSalary * 10;
  const estimate = Math.max(0, Math.round(((tenYearEarnings - totalTuition) / totalTuition) * 100));
  const payback = (totalTuition / (annualSalary * .7)).toFixed(1);
  const salary = `$${Math.round(annualSalary / 1000)}K`;
  const screenProjection = createScreenProjection(defaultScreenCorners, 600, 440);

  return (
    <section className="feature-section calculator-section motion-section" id="calculator" data-motion-section="true" data-header-theme="light" aria-labelledby="calculator-title">
      <div className="feature-shell calculator-shell">
        <div className="feature-intro calculator-intro">
          <p className="feature-label"><i /> 02 / LIVE FORECAST</p>
          <h2 id="calculator-title"><HeadlineLine>Test the <span className="oval-highlight">value</span> before</HeadlineLine><HeadlineLine>you <span className="rect-highlight lime-marker">commit.</span></HeadlineLine></h2>
          <p className="feature-description">Education is an investment. Use real data to forecast your return, compare career paths, and plan your financial future with confidence.</p>
        </div>
        
        <div className="calculator-device-viewport">
          <div ref={calculatorFrameRef} className="calculator-device-frame" style={{ "--calculator-scale": calculatorScale } as CSSProperties}>
            <div className="calculator-board ipad-device" aria-label="Interactive education ROI calculator" style={{ "--calculator-screen-transform": screenProjection } as CSSProperties}>
              <Image className="calculator-device-art" src="/fence-ipad-keyboard.png" alt="Floating iPad with keyboard displaying the education ROI calculator" width={1254} height={1254} unoptimized quality={100} priority sizes="(max-width: 720px) 100vw, (max-width: 1180px) 92vw, 920px" />

              <aside className="calculator-rail" aria-hidden="true"><b>F</b><span> ROI calculator</span><span> Career paths</span><span> Compare</span><span> Saved scenarios</span></aside>
              <div className="calculator-main">
                <header><div><h3>Education ROI Calculator</h3><p>Estimate the return from your education investment.</p></div><span className="calculator-breadcrumb">Education ▹ Outcomes ▹ You</span></header>
                <div className="calculator-form">
                  <label className="calculator-field calculator-field--select">University<div className="calculator-select-wrap"><select value={university} onChange={(event) => setUniversity(event.target.value)}><option>University of California, Berkeley</option><option>Meridian Tech</option><option>Warsaw Digital Institute</option></select></div></label>
                  <label className="calculator-field calculator-field--range">Annual tuition (USD)<output>${tuition.toLocaleString()}</output><input type="range" min="12000" max="48000" step="1000" value={tuition} style={{ "--range-progress": `${((tuition - 12000) / 36000) * 100}%` } as CSSProperties} onChange={(event) => setTuition(Number(event.target.value))} /></label>
                  <label className="calculator-field calculator-field--range">Study length <output>{years} years</output><input type="range" min="1" max="6" value={years} style={{ "--range-progress": `${((years - 1) / 5) * 100}%` } as CSSProperties} onChange={(event) => setYears(Number(event.target.value))} /></label>
                  <label className="calculator-field calculator-field--select">Career goal<div className="calculator-select-wrap"><select value={career} onChange={(event) => setCareer(event.target.value)}><option>Software Engineer</option><option>Data Analyst</option><option>UX Designer</option></select></div></label>
                  <button type="button" className="calculate-button" onClick={() => setHasCalculated(true)}> Calculate ROI <Arrow /></button>
                </div>
                <div className="calculator-results" aria-live="polite">
                  <article className="roi-result"><span>Estimated 10-year return</span><strong>{estimate}% <i></i></strong><small>{hasCalculated ? `Updated for ${university}` : "10-year earnings minus tuition"}</small></article>
                  <article className="payback-result"><span>Payback Period</span><strong>{payback} years</strong><small>Until your investment pays off</small><i className="blur-orb" aria-hidden="true" /></article>
                  <article className="salary-result"><span>Estimated Starting Salary</span><strong>{salary}</strong><small>Average annual salary in your field</small><b aria-hidden="true"></b></article>
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
  const onKeyDown = (e: any) => {
    if (e.key === 'ArrowRight') setActive(prev => Math.min(prev + 1, 2));
    if (e.key === 'ArrowLeft') setActive(prev => Math.max(prev - 1, 0));
  };
  const syncActiveToScroll = () => {};
  const swipe = {};

  return (
    <section className="feature-section comparison-section dark-feature motion-section" id="comparison" data-motion-section="true" data-header-theme="dark" aria-labelledby="comparison-title" tabIndex={0} onKeyDown={onKeyDown}>
      <div className="feature-shell comparison-shell">
        <div className="feature-intro dark-intro">
          <p className="feature-label">03 / UNIVERSITY COMPARISON</p>
          <h2 id="comparison-title"><HeadlineLine>Compare <span className="oval-highlight">more</span> than</HeadlineLine><HeadlineLine><span className="rect-highlight violet-marker">rankings.</span></HeadlineLine></h2>
          <p className="feature-description">See the real return — tuition, outcomes, scholarships, and career fit, side by side.</p>
          <div className="comparison-count"><strong>03</strong><span>Options</span><i /></div>
        </div>
        <div className="comparison-area" {...swipe}>
          <div className="university-cards" data-active={active} ref={cardsRef} onScroll={syncActiveToScroll}>
            {universities.map((university, index) => (
              <article className={`university-card university-card--${university.tone} ${active === index ? "is-active" : ""}`} key={university.name} aria-label={`${university.name}, ${active === index ? "selected" : "option"}`} data-university-index={index}>
                <button className="university-card-select" type="button" aria-label={`Select ${university.name}`} aria-pressed={active === index} onClick={() => setActive(index)} />
                <span className="university-icon" aria-hidden="true">{university.icon}</span>
                {university.best && <span className="best-fit"><i aria-hidden="true">✦</i> Best fit</span>}
                <h3>{university.name}</h3><p>{university.strap}</p>
                <dl id={`university-${index}`}><div><dt>Annual Tuition</dt><dd>{university.tuition}</dd></div><div><dt>Employment Rate</dt><dd>{university.employment}</dd></div><div><dt>Expected Salary</dt><dd>{university.salary}</dd></div><div><dt>Scholarships</dt><dd>{university.scholarship}</dd></div></dl>
                <div className="university-score"><span>Education ROI</span><strong>{university.roi}</strong><span>Career Fit Score <b>{university.fit} / 100</b></span><i><em style={{ width: `${university.fit}%` }} /></i></div>
              </article>
            ))}
          </div>
        </div>
      </div>
      <p className="sr-only" aria-live="polite">Viewing {universities[active].name}.</p>
    </section>
  );
}

const factors = [
  { name: "Location", detail: "Where you live and work matters.", delta: "+$12,240", icon: "●", salary: "$80,240" },
  { name: "Degree", detail: "Your field and level of study.", delta: "+$16,320", icon: "◇", salary: "$84,320" },
  { name: "Experience", detail: "More experience, higher earnings.", delta: "+$19,040", icon: "▣", salary: "$87,040" },
  { name: "AI impact", detail: "Understand how AI changes your field.", delta: "−$5,440", icon: "▦", salary: "$62,560" },
  { name: "Market demand", detail: "Stronger industries lift outcomes.", delta: "+$14,960", icon: "▥", salary: "$82,960" },
  { name: "Internships", detail: "Real-world experience opens doors.", delta: "+$8,160", icon: "⌁", salary: "$76,160" },
] as const;

export function OutcomeFactors({ onNavigate }: { onNavigate: Navigate }) {
  const [selected, setSelected] = useState(5);
  const factor = factors[selected];
  return (
    <section className="feature-section factors-section dark-feature motion-section" id="factors" data-motion-section="true" data-header-theme="dark" aria-labelledby="factors-title">
      <div className="feature-shell factors-shell">
        <div className="feature-intro dark-intro factors-intro"><p className="feature-label"><i /> 04 / WHAT AFFECTS YOUR FUTURE</p><h2 id="factors-title"><HeadlineLine>Your outcome</HeadlineLine><HeadlineLine>is shaped by</HeadlineLine><HeadlineLine><span className="oval-highlight">more</span> than</HeadlineLine><HeadlineLine>a degree.</HeadlineLine></h2><p className="feature-description">Explore the real factors that influence your career outcomes — and see how each choice can change your future.</p><button type="button" className="lime-button" onClick={() => onNavigate("roadmap")}>Explore your path <span><Arrow /></span></button><div className="factor-proof"><b>6<small>key factors</small></b><b>Real data<small>patterns at work</small></b><b>A clearer<small>path forward</small></b></div></div>
        <div className="factor-orbit" aria-label="Interactive career outcome factors">
          <div className="orbit-circle orbit-circle--outer" aria-hidden="true" /><div className="orbit-circle orbit-circle--middle" aria-hidden="true" /><div className="orbit-circle orbit-circle--inner" aria-hidden="true" />
          <div className="salary-core" aria-live="polite"><span>Projected salary</span><strong>{factor.salary}</strong><small>Illustrative US data analyst benchmark</small></div>
          {factors.map((item, index) => <button className={`factor-card factor-card--${index} ${selected === index ? "is-selected" : ""}`} type="button" key={item.name} aria-pressed={selected === index} onClick={() => setSelected(index)}><i aria-hidden="true">{item.icon}</i><span><b>{item.name}</b><small>{item.detail}</small></span><strong>{item.delta}</strong></button>)}
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
        <div className="roadmap-top"><div className="feature-intro"><p className="feature-label"><i /> 05 / PERSONAL CAREER ROADMAP</p><h2 id="roadmap-title"><HeadlineLine>From <span className="oval-highlight">choice</span> to</HeadlineLine><HeadlineLine><span className="rect-highlight lime-marker">first offer.</span></HeadlineLine></h2><p className="feature-description">A clear, personalized roadmap from education to real career outcomes.</p></div><div className="roadmap-metrics"><b>12 <span>months<small>to career ready</small></span></b><b>24 <span>skills<small>in demand</small></span></b><b>6 <span>projects<small>for a standout portfolio</small></span></b></div></div>
        <div className="roadmap-journey" aria-label="Five stage career roadmap" ref={journeyRef}><div className="roadmap-line" aria-hidden="true"><svg viewBox="0 0 1000 160" preserveAspectRatio="none"><path className="roadmap-line-base" pathLength="100" d="M0 133C78 133 102 87 200 87S306 52 400 52s109-45 200-45 116 45 200 45 118-22 200-22" /><path className="roadmap-line-progress" pathLength="100" style={{ strokeDashoffset: 100 - progress }} d="M0 133C78 133 102 87 200 87S306 52 400 52s109-45 200-45 116 45 200 45 118-22 200-22" /><circle cx="0" cy="133" r="11" /><circle cx="200" cy="87" r="11" /><circle cx="400" cy="52" r="12" /><circle cx="600" cy="7" r="11" /><circle cx="800" cy="52" r="11" /><circle cx="1000" cy="30" r="11" /></svg></div>{stages.map((stage, index) => <button type="button" className={`roadmap-card roadmap-card--${stage.tone} ${active === index ? "is-current" : ""}`} onClick={() => setActive(index)} aria-current={active === index ? "step" : undefined} data-roadmap-index={index} key={stage.number}><span className="roadmap-number">{stage.number}</span>{active === index && <span className="you-are">You are here</span>}<h3>{stage.title}</h3><p>{stage.text}</p><ul>{stage.checks.map((check, checkIndex) => <li className={checkIndex < Math.max(1, 3 - index) ? "done" : ""} key={check}>{check}</li>)}</ul><footer><span>Progress</span><b>{stage.progress}%</b><i><em style={{ width: `${stage.progress}%` }} /></i></footer></button>)}</div>
      </div>
    </section>
  );
}

const scholarships = [
  { title: "Future Builders Grant", copy: "Supporting the next generation of problem solvers.", amount: "$8,000", deadline: "Apr 30, 2026", country: "United States", match: 92, tags: ["Undergraduate", "STEM"], tone: "light", symbol: "✺" },
  { title: "EU Digital Talent", copy: "Empowering digital talent across Europe.", amount: "€6,500", deadline: "May 15, 2026", country: "European Union", match: 87, tags: ["Bachelor’s", "Digital Skills"], tone: "dark", symbol: "✣" },
  { title: "Women in Data Fund", copy: "Backing women building a more inclusive tech future.", amount: "$5,000", deadline: "Mar 31, 2026", country: "Global", match: 81, tags: ["Women in Tech", "Data & AI"], tone: "lime", symbol: "♧" },
  { title: "Local Innovation Award", copy: "Fueling change in local tech communities worldwide.", amount: "€3,000", deadline: "Jun 20, 2026", country: "Selected regions", match: 76, tags: ["Any level", "Social Impact"], tone: "light", symbol: "♧" },
] as const;

export function Scholarships({ onNavigate }: { onNavigate: Navigate }) {
  const [active, setActive] = useState(0);
  const carouselRef = useRef<HTMLDivElement>(null);
  const shouldScrollRef = useRef(true);
  const move = (direction: number) => {
    shouldScrollRef.current = true;
    setActive((current) => (current + direction + scholarships.length) % scholarships.length);
  };
  const swipe = useSwipe(move);
  const syncActiveToScroll = () => {
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
    shouldScrollRef.current = false;
    setActive((current) => current === nextIndex ? current : nextIndex);
  };
  const selectCard = (index: number) => {
    shouldScrollRef.current = true;
    setActive(index);
    const carousel = carouselRef.current;
    const card = carousel?.querySelector<HTMLElement>(`[data-scholarship-index="${index}"]`);
    if (carousel && card && window.matchMedia("(max-width: 700px)").matches) {
      carousel.scrollTo({ left: Math.max(0, card.offsetLeft - (carousel.clientWidth - card.offsetWidth) / 2), behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    }
  };
  useEffect(() => {
    if (!window.matchMedia("(max-width: 700px)").matches) return;
    if (!shouldScrollRef.current) return;
    shouldScrollRef.current = false;
    const carousel = carouselRef.current;
    const card = carousel?.querySelector<HTMLElement>(`[data-scholarship-index="${active}"]`);
    if (carousel && card) {
      carousel.scrollTo({ left: Math.max(0, card.offsetLeft - (carousel.clientWidth - card.offsetWidth) / 2), behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    }
  }, [active]);
  const handleCardKeyDown = (event: KeyboardEvent<HTMLElement>, index: number) => {
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); selectCard(index); }
  };
  return (
    <section className="feature-section scholarships-section motion-section" id="scholarships" data-motion-section="true" data-header-theme="light" aria-labelledby="scholarships-title">
      <div className="scholarship-crest"><span>06 / Scholarship opportunities</span><i /><span>Real funding. Brighter futures.</span></div>
      <div className="feature-shell scholarship-shell"><div className="scholarships-head"><div className="feature-intro"><h2 id="scholarships-title"><HeadlineLine><span className="oval-highlight">Funding</span></HeadlineLine><HeadlineLine>should find the</HeadlineLine><HeadlineLine>right <span className="rect-highlight lime-marker">student.</span></HeadlineLine></h2></div><p className="feature-description">Discover scholarships that match your goals, background, and future plans. Real opportunities from global organizations, in one place.</p><button className="dark-pill-button" type="button" onClick={() => onNavigate("calculator")}>Check eligibility <Arrow /></button></div>
        <div className="scholarship-carousel" data-active={active} ref={carouselRef} onScroll={syncActiveToScroll} {...swipe}>{scholarships.map((item, index) => <article className={`scholarship-card scholarship-card--${item.tone} ${active === index ? "is-active" : ""}`} key={item.title} data-scholarship-index={index} role="button" tabIndex={0} aria-label={`Select ${item.title}`} aria-pressed={active === index} onClick={() => selectCard(index)} onKeyDown={(event) => handleCardKeyDown(event, index)}><span className="scholarship-symbol" aria-hidden="true">{item.symbol}</span><h3>{item.title}</h3><p>{item.copy}</p><div className="scholarship-rule" /><div className="scholarship-amount"><span>Amount</span><strong>{item.amount}</strong></div><div className="match-ring" style={{ "--match": `${item.match * 3.6}deg` } as CSSProperties}><b>{item.match}%<small>Match</small></b></div><div className="scholarship-meta" id={`scholarship-${index}`}><span><b>Deadline</b>{item.deadline}</span><span><b>Country</b>{item.country}</span></div><div className="scholarship-tags">{item.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>{item.title === "Local Innovation Award" && <i className="blur-orb scholarship-orb" aria-hidden="true" />}</article>)}</div>
        <div className="carousel-controls scholarship-controls" role="group" aria-label="Scholarship controls"><button type="button" aria-label="Show previous scholarship" onClick={() => move(-1)}><Arrow direction="left" /></button><output aria-live="polite">{String(active + 1).padStart(2, "0")} / 04</output><button type="button" aria-label="Show next scholarship" onClick={() => move(1)}><Arrow /></button></div>
      </div>
      <p className="sr-only" aria-live="polite">Viewing {scholarships[active].title} scholarship.</p>
    </section>
  );
}

export function FinalDecision({ onNavigate }: { onNavigate: Navigate }) {
  const routes = [
    { number: "01", title: "Compare universities", copy: "See costs, outcomes, and real earning potential side by side.", target: "comparison", tone: "dark", foot: "Data, not hype" },
    { number: "02", title: "Calculate ROI", copy: "Turn tuition, time, and opportunity costs into a clear return.", target: "calculator", tone: "light", foot: "Real numbers" },
    { number: "03", title: "Build career roadmap", copy: "Explore career paths, skills, and milestones with AI guidance.", target: "roadmap", tone: "lime", foot: "From education to opportunity" },
  ];
  return <section className="feature-section final-decision-section dark-feature motion-section" id="final-decision" data-motion-section="true" data-header-theme="dark" aria-labelledby="final-decision-title"><div className="feature-shell final-shell"><div className="final-head"><p className="feature-label">08 / START WITH ONE DECISION</p><h2 id="final-decision-title"><HeadlineLine>Your future should</HeadlineLine><HeadlineLine><span className="oval-highlight">not</span> be a <span className="rect-highlight lime-marker">guess.</span></HeadlineLine></h2><p>Compare your options. Understand the returns. Build a plan that fits you.</p><button type="button" className="forecast-cta" onClick={() => onNavigate("calculator")}>Build my forecast <span><Arrow /></span></button></div><div className="decision-branches" aria-hidden="true"><i /><i /><i /></div><div className="decision-routes">{routes.map((route) => <button className={`decision-route decision-route--${route.tone}`} type="button" onClick={() => onNavigate(route.target)} key={route.number}><span>{route.number}</span><i><Arrow /></i><h3>{route.title}</h3><p>{route.copy}</p><small>{route.foot}</small></button>)}</div></div></section>;
}
