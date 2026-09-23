"use client";

import { useEffect, useRef, useState } from "react";
import { CareerRoadmap, FinalDecision, LiveRoiCalculator, OutcomeFactors, Scholarships, UniversityComparison } from "./components/FeatureSections";
import MacbookDisplay from "./components/MacbookDisplay";
import LandingFooter from "./components/LandingFooter";
import TestimonialsSection from "./components/TestimonialsSection";
import { HeadlineLine, JourneyThread, type HeaderTheme, updatePointerUnderline, useLandingMotion } from "./components/motion";

const navItems = [
  { label: "Platform", target: "comparison" },
  { label: "How it works", target: "roadmap" },
  { label: "Opportunities", target: "scholarships" },
  { label: "Calculator", target: "calculator" },
];
const navigationTargets = navItems.map((item) => item.target);

function Section({ id, theme, className, labelledBy, children }: { id: string; theme: HeaderTheme; className: string; labelledBy?: string; children: React.ReactNode }) {
  return <section className={`motion-section ${className}`} id={id} aria-labelledby={labelledBy} data-header-theme={theme} data-motion-section="true">{children}</section>;
}

export default function HomePage() {
  const pageRef = useRef<HTMLElement>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [expanded, setExpanded] = useState<"info" | null>(null);
  const [activeSection, setActiveSection] = useState("");
  const [activeHeroCard, setActiveHeroCard] = useState<number | null>(null);
  const [headerTheme, setHeaderTheme] = useState<HeaderTheme>("light");
  const [headerScrolled, setHeaderScrolled] = useState(false);

  useLandingMotion({
    pageRef,
    navigationTargets,
    onThemeChange: setHeaderTheme,
    onActiveSectionChange: setActiveSection,
    onScrolledChange: setHeaderScrolled,
  });

  // Keep the visual header state resilient to browser scroll restoration and
  // late client hydration. The RAF gate avoids a state update per raw event.
  useEffect(() => {
    let frame = 0;
    const sample = () => {
      frame = 0;
      const next = window.scrollY > 16;
      setHeaderScrolled((current) => current === next ? current : next);
    };
    const onScroll = () => {
      if (!frame) frame = window.requestAnimationFrame(sample);
    };
    sample();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("pageshow", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("pageshow", onScroll);
      if (frame) window.cancelAnimationFrame(frame);
    };
  }, []);

  useEffect(() => {
    if (!mobileOpen && !expanded) return;
    const close = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setMobileOpen(false);
      setExpanded(null);
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [expanded, mobileOpen]);

  const goTo = (target: string) => {
    setMobileOpen(false);
    const element = document.getElementById(target);
    if (!element) return;
    const headerHeight = document.querySelector<HTMLElement>(".landing-header")?.offsetHeight ?? 0;
    window.scrollTo({ top: Math.max(0, element.getBoundingClientRect().top + window.scrollY - headerHeight - 12), behavior: "smooth" });
  };
  const toggleInfo = () => setExpanded((current) => current === "info" ? null : "info");
  const onInfoCardKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    toggleInfo();
  };
  const selectHeroCard = (index: number) => setActiveHeroCard((current) => current === index ? null : index);
  const onHeroCardKeyDown = (event: React.KeyboardEvent<HTMLElement>, index: number) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    selectHeroCard(index);
  };

  return <main className="landing-page" ref={pageRef}>
    <JourneyThread />
    <header className={`landing-header ${mobileOpen ? "menu-open" : ""} ${headerScrolled ? "is-scrolled" : ""}`} data-theme={headerTheme}>
      <a className="brand" href="#hero" onClick={(event) => { event.preventDefault(); goTo("hero"); }} aria-label="Fence home"><span className="brand-mark">F</span><span className="brand-name">Fence</span><small>demo</small></a>
      <nav className="desktop-nav" aria-label="Primary navigation">{navItems.map((item) => <button className={activeSection === item.target ? "is-active" : ""} key={item.label} type="button" onPointerMove={updatePointerUnderline} onPointerLeave={(event) => event.currentTarget.style.setProperty("--pointer-x", "50%") } onClick={() => goTo(item.target)}>{item.label}</button>)}</nav>
      <div className="header-actions"><a className="login-link" href="http://127.0.0.1:8122/api/auth/login/google" onPointerMove={updatePointerUnderline} onPointerLeave={(event) => event.currentTarget.style.setProperty("--pointer-x", "50%")}>Log in</a><button className="header-cta" type="button" onClick={() => goTo("calculator")}>Get started <span aria-hidden="true">↗</span></button><button className="menu-toggle" type="button" aria-expanded={mobileOpen} aria-controls="mobile-navigation" onClick={() => setMobileOpen((open) => !open)}>{mobileOpen ? "×" : "☰"}<span className="sr-only">Menu</span></button></div>
      <nav id="mobile-navigation" className="mobile-nav" aria-label="Mobile navigation">{navItems.map((item) => <button key={item.label} type="button" onClick={() => goTo(item.target)}>{item.label}</button>)}<a href="http://127.0.0.1:8122/api/auth/login/google">Log in</a><button type="button" onClick={() => goTo("calculator")}>Get started ↗</button></nav>
    </header>

    <Section id="hero" theme="light" className="hero-section" labelledBy="hero-title">
      <div className="hero-content">
        <div className="hero-copy">
          <p className="eyebrow">EDUCATION ROI, MADE CLEAR</p>
          <h1 id="hero-title">
            <HeadlineLine>Make a smarter</HeadlineLine>
            <HeadlineLine><span className="violet-highlight">education</span></HeadlineLine>
            <HeadlineLine>decision.</HeadlineLine>
          </h1>
          <div className={`info-card ${expanded === "info" ? "expanded" : ""}`} role="button" tabIndex={0} aria-expanded={expanded === "info"} aria-controls="info-details" onClick={toggleInfo} onKeyDown={onInfoCardKeyDown}>
            <p>Tuition, payback,<br />future paths.</p>
            <div className="tag-row"><span>ROI clarity</span><span>Career fit</span></div>
            <div className="expand-copy" id="info-details">A single view of the costs, return, and next steps behind your education decision.</div>
          </div>
        </div>

        <div className="dashboard-stage" aria-label="Education ROI dashboard preview">
          <div className="dashboard-float-group">
            <div className="dashboard-device macbook-device"><MacbookDisplay /></div>
            <div className="iphone-device" aria-label="Fence mobile dashboard preview">
              <div className="iphone-screen">
                <span className="iphone-notch" aria-hidden="true" />
                <div className="iphone-status"><span>9:41</span><span>▮▮▮ ◉</span></div>
                <div className="iphone-appbar"><span><b>F</b> Fence</span><span>•••</span></div>
                <p className="iphone-greeting">Your next move,<br /><strong>Andrii.</strong></p>
                <div className="iphone-scenario"><small>YOUR ACTIVE SCENARIO</small><strong>Computer<br />Science</strong><span>Rzeszów · On campus</span><i aria-hidden="true" /></div>
                <div className="iphone-stats"><div><strong>442%</strong><span>ROI</span></div><div><strong>4.3y</strong><span>PAYBACK</span></div></div>
                <div className="iphone-roadmap"><small>CAREER ROADMAP</small><strong>3 of 12 tasks</strong><span><i /></span></div>
              </div>
            </div>
            <div className="overlay-bento">
              <div className={`bento-card bento-card--grey bento-card--tall ${activeHeroCard === 0 ? "is-active" : ""}`} role="button" tabIndex={0} aria-pressed={activeHeroCard === 0} aria-label="Select invoice validation metric" onClick={() => selectHeroCard(0)} onKeyDown={(event) => onHeroCardKeyDown(event, 0)}>
                <div className="bento-art bento-art--wave">
                  <div className="bento-wave-bg" />
                </div>
                <div className="bento-copy">
                  <strong>100%</strong>
                  <span>invoice validation<br />accuracy</span>
                </div>
              </div>
              
              <div className={`bento-card bento-card--lime bento-card--tall ${activeHeroCard === 1 ? "is-active" : ""}`} role="button" tabIndex={0} aria-pressed={activeHeroCard === 1} aria-label="Select faster cycle metric" onClick={() => selectHeroCard(1)} onKeyDown={(event) => onHeroCardKeyDown(event, 1)}>
                <div className="bento-topline">
                  <div className="bento-faces">
                    <span className="face face-1"></span>
                    <span className="face face-2"></span>
                    <span className="face face-3"></span>
                    <span className="face face-4"></span>
                  </div>
                  <span aria-hidden="true" className="bento-arrow-btn">↗</span>
                </div>
                <div className="bento-copy bento-copy--push">
                  <strong>70%</strong>
                  <span>faster cycle<br />times</span>
                </div>
              </div>

              <div className="bento-col">
                <div className={`bento-card bento-card--white ${activeHeroCard === 2 ? "is-active" : ""}`} role="button" tabIndex={0} aria-pressed={activeHeroCard === 2} aria-label="Select automated processes metric" onClick={() => selectHeroCard(2)} onKeyDown={(event) => onHeroCardKeyDown(event, 2)}>
                  <div className="bento-orb"></div>
                  <div className="bento-copy">
                    <strong>80%+</strong>
                    <span>processes<br />automated</span>
                  </div>
                </div>
                
                <div className={`bento-card bento-card--black ${activeHeroCard === 3 ? "is-active" : ""}`} role="button" tabIndex={0} aria-pressed={activeHeroCard === 3} aria-label="Select deployment metric" onClick={() => selectHeroCard(3)} onKeyDown={(event) => onHeroCardKeyDown(event, 3)}>
                  <div className="bento-copy bento-copy--row">
                    <strong>4</strong>
                    <span>weeks - average<br />deployment<br />per domain</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="section-index"><span>01</span><i /><span>FENCE / DEMO</span></div>
    </Section>
    <LiveRoiCalculator />
    <UniversityComparison />
    <OutcomeFactors onNavigate={goTo} />
    <CareerRoadmap />
    <Scholarships onNavigate={goTo} />
    <TestimonialsSection onExplore={() => goTo("roadmap")} />
    <FinalDecision onNavigate={goTo} />
    <LandingFooter onNavigate={goTo} />
  </main>;
}
