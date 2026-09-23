import { useEffect, useRef, useState, type CSSProperties, type MutableRefObject, type PointerEvent as ReactPointerEvent, type ReactNode } from "react";

export type HeaderTheme = "light" | "dark";

type LandingMotionOptions = {
  pageRef: MutableRefObject<HTMLElement | null>;
  navigationTargets: readonly string[];
  onThemeChange: (theme: HeaderTheme) => void;
  onActiveSectionChange: (section: string) => void;
  onScrolledChange: (scrolled: boolean) => void;
};

export function HeadlineLine({ children }: { children: ReactNode }) {
  return <span className="headline-line"><span>{children}</span></span>;
}

/**
 * One normalized route connects the landing chapters. It deliberately lives
 * in the outer composition lane, so it remains continuous without cutting
 * through the editorial reading areas as the layout reflows.
 */
export function JourneyThread() {
  // These normalized bands sit in the breathing space of each chapter and
  // line up with the major surface changes as the composition reflows.
  const contourBands = [68, 194, 306, 418, 530, 642, 758, 870, 958];
  const contourOffsets = [0, 8, 16, 24];
  const ambientWaveBands = [810, 846, 882];

  const contourPath = (band: number, offset: number) => {
    const y = band + offset;
    return `M -4 ${y} C 8 ${y - 18} 18 ${y - 18} 31 ${y} S 54 ${y + 18} 68 ${y} S 91 ${y - 18} 104 ${y}`;
  };

  // A deterministic distribution gives every landing chapter several signal
  // dots without introducing random server/client differences.
  const dotColors = ["lime", "dark", "violet"] as const;
  const dotScales = [.72, .9, 1.08, .82, .96] as const;
  const signalDots = Array.from({ length: 36 }, (_, index) => ({
    x: 4 + ((index * 37) % 92),
    y: 1.8 + index * (96.4 / 35),
    scale: dotScales[index % dotScales.length],
    color: dotColors[index % dotColors.length],
  }));

  return <div className="journey-thread" aria-hidden="true"><svg viewBox="0 0 100 1000" preserveAspectRatio="none">
    <g className="journey-thread__contours">
      {contourBands.flatMap((band) => contourOffsets.map((offset) => (
        <path key={`${band}-${offset}`} className="journey-thread__contour" d={contourPath(band, offset)} />
      )))}
    </g>
    <g className="journey-thread__ambient-waves">
      {ambientWaveBands.map((band) => (
        <path key={band} d={`M -4 ${band} C 10 ${band - 54} 22 ${band - 54} 36 ${band} S 62 ${band + 54} 76 ${band} S 98 ${band - 54} 104 ${band}`} />
      ))}
    </g>
  </svg><span className="journey-page-dots" aria-hidden="true">
    {signalDots.map(({ x, y, scale, color }, index) => (
      <i
        key={index}
        className={`journey-page-dot dot-${color}`}
        style={{ "--dot-x": `${x}%`, "--dot-y": `${y}%`, "--dot-scale": scale } as CSSProperties}
      />
    ))}
  </span></div>;
}

export function updatePointerUnderline(event: ReactPointerEvent<HTMLElement>) {
  const target = event.currentTarget;
  const bounds = target.getBoundingClientRect();
  target.style.setProperty("--pointer-x", `${event.clientX - bounds.left}px`);
}

export function useReducedMotion() {
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReducedMotion(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  return reducedMotion;
}

/**
 * Shared SectionThemeObserver + ScrollParallaxLayer for the landing journey.
 * Continuous values live in CSS variables; React only receives discrete changes.
 */
export function useLandingMotion({ pageRef, navigationTargets, onThemeChange, onActiveSectionChange, onScrolledChange }: LandingMotionOptions) {
  const reducedMotion = useReducedMotion();
  const themeRef = useRef<HeaderTheme>("light");
  const activeRef = useRef("");
  const scrolledRef = useRef(false);

  useEffect(() => {
    const page = pageRef.current;
    if (!page) return;

    const sections = Array.from(page.querySelectorAll<HTMLElement>("[data-motion-section]"));
    const hero = page.querySelector<HTMLElement>("#hero");
    const heroStage = hero?.querySelector<HTMLElement>(".dashboard-stage");
    const testimonials = page.querySelector<HTMLElement>("#testimonials");
    const depthTargets = Array.from(page.querySelectorAll<HTMLElement>(".dashboard-stage, .calculator-board, .roadmap-journey, .factor-orbit, .testimonials-stage, .decision-routes"));
    const textTargets = Array.from(page.querySelectorAll<HTMLElement>(".motion-section .eyebrow, .motion-section h2, .motion-section .feature-description, .motion-section .path-description, .motion-section .testimonials-description, .motion-section .final-head > p"));
    let frame = 0;

    const update = (reveal = true) => {
      frame = 0;
      const heroStageRect = heroStage?.getBoundingClientRect();
      const heroExit = Math.max(0, Math.min(1, -(hero?.getBoundingClientRect().top ?? 0) / Math.max(1, (hero?.offsetHeight ?? window.innerHeight) * .72)));
      const testimonialsTop = testimonials?.getBoundingClientRect().top ?? window.innerHeight;
      const testimonialsProgress = Math.max(0, Math.min(1, (window.innerHeight * .88 - testimonialsTop) / (window.innerHeight * 1.08)));
      const pageProgress = Math.max(0, Math.min(1, window.scrollY / Math.max(1, document.documentElement.scrollHeight - window.innerHeight)));
      const contourDrift = reducedMotion ? 0 : Math.sin(pageProgress * Math.PI * 2) * 14;

      page.style.setProperty("--page-progress", pageProgress.toFixed(3));
      page.style.setProperty("--journey-progress", pageProgress.toFixed(3));
      page.style.setProperty("--contour-drift", `${contourDrift.toFixed(2)}px`);
      depthTargets.forEach((target) => {
        const rect = target.getBoundingClientRect();
        const distance = (window.innerHeight * .52 - (rect.top + rect.height * .5)) / Math.max(window.innerHeight, rect.height);
        const depth = reducedMotion ? 0 : Math.max(-12, Math.min(12, Math.round(distance * 10)));
        target.style.setProperty("--scroll-depth", `${depth}px`);
      });
      textTargets.forEach((target) => {
        const rect = target.getBoundingClientRect();
        const distance = (window.innerHeight * .52 - (rect.top + rect.height * .5)) / Math.max(window.innerHeight, rect.height);
        const shift = reducedMotion ? 0 : Math.max(-10, Math.min(10, Math.round(distance * 6)));
        target.style.setProperty("--scroll-text-shift", `${shift}px`);
      });
      page.style.setProperty("--hero-shift", reducedMotion ? "0px" : `${Math.round(heroExit * -44)}px`);
      page.style.setProperty("--hero-scale", reducedMotion ? "1" : `${(1 - heroExit * .025).toFixed(3)}`);
      page.style.setProperty("--testimonials-progress", testimonialsProgress.toFixed(3));
      page.style.setProperty("--testimonials-lime-lift", reducedMotion ? "0px" : `${Math.round((1 - testimonialsProgress) * 42)}px`);
      page.style.setProperty("--testimonials-light-lift", reducedMotion ? "0px" : `${Math.round((1 - testimonialsProgress) * -32)}px`);
      page.style.setProperty("--testimonials-dark-lift", reducedMotion ? "0px" : `${Math.round((1 - testimonialsProgress) * 46)}px`);
      page.style.setProperty("--testimonials-quote-shift", reducedMotion ? "0px" : `${Math.round((1 - testimonialsProgress) * 18)}px`);

      // Keep the product scene hidden until its leading edge reaches the
      // viewport midpoint. Hide it again as it leaves through the top while
      // scrolling into the next chapter.
      const heroVisualVisible = Boolean(
        heroStageRect
        && heroStageRect.top <= window.innerHeight * .5
        && heroStageRect.bottom > window.innerHeight * .22,
      );
      hero?.classList.toggle("is-visual-visible", heroVisualVisible);

      const scrolled = window.scrollY > 16;
      if (scrolled !== scrolledRef.current) {
        scrolledRef.current = scrolled;
        onScrolledChange(scrolled);
      }

      if (reveal) {
        sections.forEach((section) => {
          const rect = section.getBoundingClientRect();
          // The footer is keyed to the CTA itself, not the footer container:
          // reveal when "Ready to decide?" crosses the line 16% above the
          // viewport bottom (84% from the top).
          const footerCard = section.id === "footer"
            ? section.querySelector<HTMLElement>(".footer-ready-card")
            : null;
          const triggerRect = footerCard?.getBoundingClientRect() ?? rect;
          const revealLine = section.id === "footer"
            ? window.innerHeight * .75
            : window.innerHeight * .5;
          // Use the CTA as the entrance trigger, but keep the footer visible
          // while its section remains on screen. At the document bottom the
          // CTA may be above the viewport even though the footer is still visible.
          const isInView = section.id === "footer"
            ? triggerRect.top < revealLine && rect.bottom > 0
            : triggerRect.top < revealLine && triggerRect.bottom > revealLine;
          section.classList.toggle("is-visible", isInView);
        });
      }

      const anchor = window.innerWidth < 900 ? 76 : 92;
      const current = sections.find((section) => {
        const rect = section.getBoundingClientRect();
        return rect.top <= anchor && rect.bottom > anchor;
      }) ?? sections[0];
      const theme = (current?.dataset.headerTheme as HeaderTheme) || "light";
      if (theme !== themeRef.current) {
        themeRef.current = theme;
        onThemeChange(theme);
      }

      const navigationTarget = current?.id ?? "";
      const active = navigationTargets.includes(navigationTarget) ? navigationTarget : "";
      if (active !== activeRef.current) {
        activeRef.current = active;
        onActiveSectionChange(active);
      }
    };

    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(() => update());
    };
    const observer = new IntersectionObserver(
      (entries) => entries.forEach((entry) => {
        // Footer uses the scroll-sampled 25%-from-bottom guide line above; the
        // shared observer root margin is intentionally kept for main sections.
        if (["hero", "footer"].includes((entry.target as HTMLElement).id)) return;
        entry.target.classList.toggle("is-visible", entry.isIntersecting);
      }),
      { threshold: .1, rootMargin: "0px 0px -50% 0px" },
    );

    // Establish scroll/theme variables first, but leave sections unrevealed for
    // one paint. This guarantees that the first visible headings animate instead
    // of receiving is-visible before their initial hidden state is applied.
    update(false);
    page.dataset.reducedMotion = String(reducedMotion);
    page.classList.add("js-ready");
    sections.forEach((section) => observer.observe(section));
    // Browsers can restore scroll after the first client effect. Sample once more
    // on the next frame and on pageshow so the reveal and header state stay synced.
    let restoreFrame = requestAnimationFrame(() => update());
    const restoreTimeout = window.setTimeout(update, 180);
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    window.addEventListener("pageshow", onScroll);

    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      window.removeEventListener("pageshow", onScroll);
      observer.disconnect();
      window.clearTimeout(restoreTimeout);
      if (frame) cancelAnimationFrame(frame);
      cancelAnimationFrame(restoreFrame);
    };
  }, [navigationTargets, onActiveSectionChange, onScrolledChange, onThemeChange, pageRef, reducedMotion]);

  return reducedMotion;
}
