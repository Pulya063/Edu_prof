"use client";

import { useEffect, useState } from "react";

export type SectionLink = { id: string; label: string };

/** Sticky in-page navigation; highlights the section currently in view. */
export default function SectionNav({ sections }: { sections: SectionLink[] }) {
  const [active, setActive] = useState(sections[0]?.id ?? "");

  useEffect(() => {
    const elements = sections.map((section) => document.getElementById(section.id)).filter((element): element is HTMLElement => element != null);
    if (!elements.length) return;
    // A section counts as current once its top passes the upper third of the viewport.
    const observer = new IntersectionObserver((entries) => {
      const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
      if (visible[0]) setActive(visible[0].target.id);
    }, { rootMargin: "-130px 0px -60% 0px" });
    elements.forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, [sections]);

  function jump(event: React.MouseEvent<HTMLAnchorElement>, id: string) {
    const target = document.getElementById(id);
    if (!target) return;
    event.preventDefault();
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    target.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
    window.history.replaceState(window.history.state, "", `#${id}`);
    setActive(id);
  }

  return (
    <nav className="section-nav" aria-label="Calculation sections">
      {sections.map((section) => (
        <a key={section.id} href={`#${section.id}`} aria-current={active === section.id ? "true" : undefined} onClick={(event) => jump(event, section.id)}>
          {section.label}
        </a>
      ))}
    </nav>
  );
}
