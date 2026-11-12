"use client";

import { useEffect, useRef } from "react";

/**
 * Lime bar under a nav that slides to the link under the pointer (or keyboard focus) and
 * settles back on the current page's link. The nav renders `<span className="nav-indicator" />`;
 * this hook only writes --ind-x / --ind-w and data-indicator on the nav element.
 */
export function useNavIndicator<T extends HTMLElement>() {
  const ref = useRef<T>(null);

  useEffect(() => {
    const nav = ref.current;
    if (!nav) return;
    const place = (link: HTMLElement | null) => {
      if (!link) {
        nav.dataset.indicator = "off";
        return;
      }
      nav.style.setProperty("--ind-x", `${link.offsetLeft}px`);
      nav.style.setProperty("--ind-w", `${link.offsetWidth}px`);
      nav.dataset.indicator = "on";
    };
    const rest = () => place(nav.querySelector<HTMLElement>('a[aria-current="page"]'));
    const follow = (event: Event) => {
      const link = (event.target as HTMLElement | null)?.closest("a");
      if (link && nav.contains(link)) place(link);
    };
    nav.addEventListener("pointerover", follow);
    nav.addEventListener("focusin", follow);
    nav.addEventListener("pointerleave", rest);
    nav.addEventListener("focusout", rest);
    window.addEventListener("resize", rest);
    rest();
    return () => {
      nav.removeEventListener("pointerover", follow);
      nav.removeEventListener("focusin", follow);
      nav.removeEventListener("pointerleave", rest);
      nav.removeEventListener("focusout", rest);
      window.removeEventListener("resize", rest);
    };
  }, []);

  return ref;
}
