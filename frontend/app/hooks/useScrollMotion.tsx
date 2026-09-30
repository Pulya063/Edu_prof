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

  const optionsRef = useRef({ navigationTargets, onThemeChange, onActiveSectionChange, onScrolledChange });
  useEffect(() => {
    optionsRef.current = { navigationTargets, onThemeChange, onActiveSectionChange, onScrolledChange };
  }, [navigationTargets, onThemeChange, onActiveSectionChange, onScrolledChange]);

  useEffect(() => {
    const page = pageRef.current;
    if (!page) return;

    const sections = Array.from(page.querySelectorAll<HTMLElement>("[data-motion-section]"));
    // Keep scroll depth on a stable wrapper. Applying it to the iPad itself
    // would continuously restart the device reveal transition while scrolling.
    const depthTargets = Array.from(page.querySelectorAll<HTMLElement>(".calculator-device-frame, .decision-routes"));
    const textTargets = Array.from(page.querySelectorAll<HTMLElement>(".motion-section .eyebrow, .motion-section h2, .motion-section .feature-description, .motion-section .path-description, .motion-section .testimonials-description, .motion-section .final-head > p"));
    const hero = page.querySelector<HTMLElement>("#hero");
    const heroStage = hero?.querySelector<HTMLElement>(".dashboard-stage");
    const calculator = page.querySelector<HTMLElement>("#calculator");
    const calculatorFrame = calculator?.querySelector<HTMLElement>(".calculator-device-frame");
    const deviceFrames = [
      hero && heroStage ? { section: hero, frame: heroStage } : null,
      calculator && calculatorFrame ? { section: calculator, frame: calculatorFrame } : null,
    ].filter((item): item is { section: HTMLElement; frame: HTMLElement } => item !== null);
    const header = page.querySelector<HTMLElement>(".landing-header");
    const testimonials = page.querySelector<HTMLElement>("#testimonials");
    const footer = sections.find((section) => section.id === "footer");
    const footerCard = footer?.querySelector<HTMLElement>(".footer-ready-card");
    let frame = 0;

    const update = (reveal = true) => {
      frame = 0;
      const viewportHeight = window.innerHeight;
      const viewportWidth = window.innerWidth;
      const scrollY = window.scrollY;
      const documentHeight = document.documentElement.scrollHeight;
      const heroRect = hero?.getBoundingClientRect();
      const headerRect = header?.getBoundingClientRect();
      const testimonialsTop = testimonials?.getBoundingClientRect().top ?? viewportHeight;
      const depthRects = depthTargets.map((target) => ({ target, rect: target.getBoundingClientRect() }));
      const textRects = textTargets.map((target) => ({ target, rect: target.getBoundingClientRect() }));
      const sectionRects = sections.map((section) => ({
        section,
        rect: section.getBoundingClientRect(),
        triggerRect: section === footer && footerCard ? footerCard.getBoundingClientRect() : null,
      }));
      const deviceFrameRects = deviceFrames.map(({ section, frame: deviceFrame }) => ({
        section,
        rect: deviceFrame.getBoundingClientRect(),
      }));
      const heroExit = Math.max(0, Math.min(1, -(heroRect?.top ?? 0) / Math.max(1, (hero?.offsetHeight ?? viewportHeight) * .72)));
      const testimonialsProgress = Math.max(0, Math.min(1, (viewportHeight * .88 - testimonialsTop) / (viewportHeight * 1.08)));
      const pageProgress = Math.max(0, Math.min(1, scrollY / Math.max(1, documentHeight - viewportHeight)));
      const contourDrift = reducedMotion ? 0 : Math.sin(pageProgress * Math.PI * 2) * 14;

      page.style.setProperty("--page-progress", pageProgress.toFixed(3));
      page.style.setProperty("--journey-progress", pageProgress.toFixed(3));
      page.style.setProperty("--contour-drift", `${contourDrift.toFixed(2)}px`);
      depthRects.forEach(({ target, rect }) => {
        const distance = (viewportHeight * .52 - (rect.top + rect.height * .5)) / Math.max(viewportHeight, rect.height);
        const isCompactDevice = viewportWidth <= 720 && target.classList.contains("calculator-device-frame");
        const depthLimit = isCompactDevice ? 5 : 12;
        const depthFactor = isCompactDevice ? 4 : 10;
        const depth = reducedMotion ? 0 : Math.max(-depthLimit, Math.min(depthLimit, distance * depthFactor));
        target.style.setProperty("--scroll-depth", `${depth.toFixed(2)}px`);
      });
      textRects.forEach(({ target, rect }) => {
        const distance = (viewportHeight * .52 - (rect.top + rect.height * .5)) / Math.max(viewportHeight, rect.height);
        const shift = reducedMotion ? 0 : Math.max(-10, Math.min(10, distance * 6));
        target.style.setProperty("--scroll-text-shift", `${shift.toFixed(2)}px`);
      });
      page.style.setProperty("--hero-shift", reducedMotion ? "0px" : `${(heroExit * -44).toFixed(2)}px`);
      page.style.setProperty("--hero-scale", reducedMotion ? "1" : `${(1 - heroExit * .025).toFixed(3)}`);
      page.style.setProperty("--testimonials-progress", testimonialsProgress.toFixed(3));
      page.style.setProperty("--testimonials-lime-lift", reducedMotion ? "0px" : `${((1 - testimonialsProgress) * 42).toFixed(2)}px`);
      page.style.setProperty("--testimonials-light-lift", reducedMotion ? "0px" : `${((1 - testimonialsProgress) * -32).toFixed(2)}px`);
      page.style.setProperty("--testimonials-dark-lift", reducedMotion ? "0px" : `${((1 - testimonialsProgress) * 46).toFixed(2)}px`);
      page.style.setProperty("--testimonials-quote-shift", reducedMotion ? "0px" : `${((1 - testimonialsProgress) * 18).toFixed(2)}px`);

      // Devices use one symmetric visibility state for motion in and out.
      // The measurements are refreshed by the shared scroll/resize RAF path,
      // including ResizeObserver, visualViewport and orientation changes.
      deviceFrameRects.forEach(({ section, rect }) => {
        const isDeviceVisible = rect.top < viewportHeight * .94 && rect.bottom > viewportHeight * .06;
        section.classList.toggle("is-device-visible", reducedMotion || isDeviceVisible);
      });

      const scrolled = window.scrollY > 16;
      if (scrolled !== scrolledRef.current) {
        scrolledRef.current = scrolled;
        optionsRef.current.onScrolledChange(scrolled);
      }

      if (reveal) {
        // The observer owns reveals for main sections; keep only hero/footer on
        // the custom guide line so the same class is never toggled by two systems.
        sectionRects.forEach(({ section, rect, triggerRect }) => {
          if (section !== hero && section !== footer) return;
          const revealLine = section === footer ? viewportHeight * .75 : viewportHeight * .5;
          const activeRect = triggerRect ?? rect;
          const isInView = section === footer
            ? activeRect.top < revealLine && rect.bottom > 0
            : activeRect.top < revealLine && activeRect.bottom > revealLine;
          section.classList.toggle("is-visible", isInView);
        });
      }

      const anchor = (headerRect?.bottom ?? (viewportWidth < 900 ? 76 : 92)) + 16;
      const current = sectionRects.find(({ rect }) => rect.top <= anchor && rect.bottom > anchor)?.section ?? sections[0];
      const theme = (current?.dataset.headerTheme as HeaderTheme) || "light";
      if (theme !== themeRef.current) {
        themeRef.current = theme;
        optionsRef.current.onThemeChange(theme);
      }

      const navigationTarget = current?.id ?? "";
      const active = optionsRef.current.navigationTargets.includes(navigationTarget) ? navigationTarget : "";
      if (active !== activeRef.current) {
        activeRef.current = active;
        optionsRef.current.onActiveSectionChange(active);
      }
    };

    const scheduleUpdate = () => {
      if (!frame) frame = requestAnimationFrame(() => update());
    };
    const observer = new IntersectionObserver(
      (entries) => entries.forEach((entry) => {
        // Footer uses the scroll-sampled 25%-from-bottom guide line above; the
        // shared observer root margin is intentionally kept for main sections.
        if (["hero", "footer"].includes((entry.target as HTMLElement).id)) return;
        entry.target.classList.toggle("is-visible", entry.isIntersecting);
      }),
      // FIX: -30% instead of -50% so sections animate in sooner on scroll
      { threshold: .08, rootMargin: "0px 0px -30% 0px" },
    );

    // FIX: Set is-visible (with reveal=true) BEFORE adding js-ready.
    // Old order was: update(false) → js-ready → RAF update(true), which caused
    // one frame where hero elements were opacity:0 with no animation yet.
    // Now: update(true) sets hero/footer visibility → pre-mark any other section
    // already in viewport → THEN js-ready — zero flash guaranteed.
    update(true);
    page.dataset.reducedMotion = String(reducedMotion);

    // Pre-mark non-hero/footer sections that are already in the viewport so
    // js-ready doesn't hide them for even one frame before the observer fires.
    const vh = window.innerHeight;
    sections.forEach((section) => {
      if (section === hero || section === footer) return;
      const rect = section.getBoundingClientRect();
      // Section is meaningfully visible: top above 70% of viewport
      if (rect.top < vh * 0.7 && rect.bottom > vh * 0.1) {
        section.classList.add("is-visible");
      }
      observer.observe(section);
    });

    page.classList.add("js-ready");

    // Browsers can restore scroll after the first client effect. Sample once more
    // on the next frame and on pageshow so the reveal and header state stay synced.
    let restoreFrame = requestAnimationFrame(() => update());
    const restoreTimeout = window.setTimeout(update, 180);
    const resizeObserver = new ResizeObserver(scheduleUpdate);
    resizeObserver.observe(page);
    window.addEventListener("scroll", scheduleUpdate, { passive: true });
    window.addEventListener("resize", scheduleUpdate);
    window.addEventListener("orientationchange", scheduleUpdate);
    window.addEventListener("pageshow", scheduleUpdate);
    window.visualViewport?.addEventListener("resize", scheduleUpdate);

    return () => {
      window.removeEventListener("scroll", scheduleUpdate);
      window.removeEventListener("resize", scheduleUpdate);
      window.removeEventListener("orientationchange", scheduleUpdate);
      window.removeEventListener("pageshow", scheduleUpdate);
      window.visualViewport?.removeEventListener("resize", scheduleUpdate);
      resizeObserver.disconnect();
      observer.disconnect();
      window.clearTimeout(restoreTimeout);
      if (frame) cancelAnimationFrame(frame);
      cancelAnimationFrame(restoreFrame);
    };
  }, [pageRef, reducedMotion]);

  return reducedMotion;
}
