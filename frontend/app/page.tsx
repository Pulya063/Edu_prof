"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { CareerRoadmap, FinalDecision, LiveRoiCalculator, OutcomeFactors, Scholarships, UniversityComparison } from "./components/Features";
import MacbookDisplay from "./components/MacbookDisplay";
import LandingFooter from "./components/LandingFooter";
import TestimonialsSection from "./components/TestimonialsSection";
import { HeadlineLine, JourneyThread, type HeaderTheme, useLandingMotion } from "./hooks/useScrollMotion";
import { useLanguage } from "./context/LanguageContext";
import { translations } from "./utils/translations";
import type { Lang } from "./context/LanguageContext";

// Nav items are derived from translations at render time
const navTargets = ["comparison", "roadmap", "scholarships", "calculator"];
const ignoreActiveSectionChange = (_section: string) => undefined;

function Section({ id, theme, className, labelledBy, children }: { id: string; theme: HeaderTheme; className: string; labelledBy?: string; children: React.ReactNode }) {
  return <section className={`motion-section ${className}`} id={id} aria-labelledby={labelledBy} data-header-theme={theme} data-motion-section="true">{children}</section>;
}

/** Language selector dropdown */
function LangSwitcher() {
  const { lang, setLang } = useLanguage();
  const t = translations[lang];
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const closeKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", closeKey);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", closeKey);
    };
  }, [open]);

  const LANGS: Lang[] = ["en", "uk", "pl"];
  const CODES: Record<Lang, string> = { en: "EN", uk: "UA", pl: "PL" };

  return (
    <div ref={ref} className="lang-switcher" data-open={open || undefined}>
      <button
        className="lang-switcher-trigger"
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={`Language: ${t.langLabels[lang]}`}
        onClick={() => setOpen((o) => !o)}
      >
        {CODES[lang]}
        <svg aria-hidden="true" viewBox="0 0 10 6" width="10" height="6" fill="none">
          <path d="M1 1l4 4 4-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>
      {open && (
        <ul className="lang-switcher-menu" role="listbox" aria-label="Choose language">
          {LANGS.map((l) => (
            <li key={l} role="option" aria-selected={lang === l}>
              <button
                type="button"
                className={lang === l ? "is-active" : ""}
                onClick={() => { setLang(l); setOpen(false); }}
              >
                {t.langLabels[l]}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function HomePage() {
  const pageRef = useRef<HTMLElement>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [headerTheme, setHeaderTheme] = useState<HeaderTheme>("light");
  const [headerScrolled, setHeaderScrolled] = useState(false);

  const { lang } = useLanguage();
  const t = translations[lang];

  // Build nav items from translations — no active section tracking for nav highlights
  const navItems = [
    { label: t.nav.platform, target: "comparison" },
    { label: t.nav.howItWorks, target: "roadmap" },
    { label: t.nav.opportunities, target: "scholarships" },
    { label: t.nav.calculator, target: "calculator" },
  ];

  useLandingMotion({
    pageRef,
    navigationTargets: navTargets,
    onThemeChange: setHeaderTheme,
    onActiveSectionChange: ignoreActiveSectionChange,
    onScrolledChange: setHeaderScrolled,
  });

  useEffect(() => {
    if (!mobileOpen) return;
    const close = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setMobileOpen(false);
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [mobileOpen]);

  const goTo = (target: string) => {
    setMobileOpen(false);
    const element = document.getElementById(target);
    if (!element) return;
    const headerHeight = document.querySelector<HTMLElement>(".landing-header")?.offsetHeight ?? 0;
    window.scrollTo({ top: Math.max(0, element.getBoundingClientRect().top + window.scrollY - headerHeight - 12), behavior: "smooth" });
  };

  return (
    <main className="landing-page" ref={pageRef}>
    <JourneyThread />
    <header className={`landing-header ${mobileOpen ? "menu-open" : ""} ${headerScrolled ? "is-scrolled" : ""}`} data-theme={headerTheme}>
      <a className="brand" href="#hero" onClick={(event) => { event.preventDefault(); goTo("hero"); }} aria-label="Fence home"><span className="brand-mark">F</span><span className="brand-name">Fence</span><small>preview</small></a>
      <nav className="desktop-nav" aria-label="Primary navigation">
        {navItems.map((item) => <span className="desktop-nav-label" key={item.label}>{item.label}</span>)}
      </nav>
      <div className="header-actions">
        <LangSwitcher />
        <a className="header-cta" href="/login">{t.header.signIn}</a>
        <a className="login-link" href="/register">{t.header.signUp}</a>
        <button className="menu-toggle" type="button" aria-expanded={mobileOpen} aria-controls="mobile-navigation" onClick={() => setMobileOpen((open) => !open)}><span aria-hidden="true">{mobileOpen ? "×" : "☰"}</span><span className="sr-only">Menu</span></button>
      </div>
      <nav id="mobile-navigation" className="mobile-nav" aria-label="Mobile navigation">
        {navItems.map((item) => <span className="mobile-nav-label" key={item.label}>{item.label}</span>)}
        <a className="mobile-pricing-link" href="/login">{t.header.signIn}</a>
        <a href="/register" style={{ opacity: 0.8 }}>{t.header.signUp}</a>
      </nav>
    </header>

    <Section id="hero" theme="light" className="hero-section" labelledBy="hero-title">
      <div className="hero-content">
        <div className="hero-copy">
          <p className="eyebrow">{t.hero.eyebrow}</p>
          <h1 id="hero-title"><HeadlineLine>{t.hero.h1Line1}</HeadlineLine><HeadlineLine><span className="violet-highlight">{t.hero.h1Line2}</span></HeadlineLine><HeadlineLine>{t.hero.h1Line3}</HeadlineLine></h1>
          <div className="info-card">
            <p>{t.hero.infoCardP.split("\n").map((line, i) => i === 0 ? <span key={i}>{line}<br /></span> : <span key={i}>{line}</span>)}</p>
            <div className="tag-row"><span>{t.hero.tagRoi}</span><span>{t.hero.tagCareer}</span></div>
          </div>
        </div>
        <div className="dashboard-stage" aria-label="Education ROI dashboard preview">
          <div className="dashboard-float-group">
            <div className="dashboard-device macbook-device"><MacbookDisplay /></div>
            <div className="iphone-device" aria-label="Fence mobile dashboard preview"><div className="iphone-screen"><span className="iphone-notch" aria-hidden="true" /><div className="iphone-status"><span>9:41</span><span>▮▮▮ ◉</span></div><div className="iphone-appbar"><span><b>F</b> Fence</span><span>•••</span></div><p className="iphone-greeting">Your next move,<br /><strong>Andrii.</strong></p><div className="iphone-scenario"><small>YOUR ACTIVE SCENARIO</small><strong>Computer<br />Science</strong><span>Rzeszów · On campus</span><i aria-hidden="true" /></div><div className="iphone-stats"><div><strong>442%</strong><span>ROI</span></div><div><strong>4.3y</strong><span>PAYBACK</span></div></div><div className="iphone-roadmap"><small>CAREER ROADMAP</small><strong>3 of 12 tasks</strong><span><i /></span></div></div></div>
            <div className="overlay-bento">
              <div className="bento-card bento-card--grey bento-card--tall">
                <div className="bento-art bento-art--wave">
                  <div className="bento-wave-bg" />
                </div>
                <div className="bento-copy">
                  <strong>$53k</strong>
                  <span>example net<br />education cost</span>
                </div>
              </div>

              <div className="bento-card bento-card--lime bento-card--tall">
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
                  <strong>4.3y</strong>
                  <span>illustrative<br />payback period</span>
                </div>
              </div>

              <div className="bento-col">
                <div className="bento-card bento-card--white">
                  <div className="bento-orb"></div>
                  <div className="bento-copy">
                    <strong>89%</strong>
                    <span>employment<br />assumption</span>
                  </div>
                </div>

                <div className="bento-card bento-card--black">
                  <div className="bento-copy bento-copy--row">
                    <strong>12</strong>
                    <span>skills and<br />experience<br />steps</span>
                  </div>
                </div>
              </div>
            </div></div></div></div>
        <div className="section-index"><span>01</span><i /><span>FENCE / DECISION PREVIEW</span></div>
      </Section>
    <LiveRoiCalculator />
    <UniversityComparison />
    <OutcomeFactors />
    <CareerRoadmap />
    <Scholarships />
    <TestimonialsSection />
    <FinalDecision />
    <LandingFooter />
  </main>);
}
