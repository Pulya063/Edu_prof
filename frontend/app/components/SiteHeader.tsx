"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { useLanguage } from "../context/LanguageContext";
import { translations } from "../utils/translations";
import { SITE_NAV } from "./siteNav";
import { useNavIndicator } from "./useNavIndicator";

import Link from "next/link";
/** Header for public sub-pages (calculation, about, contact, legal). The landing keeps its own animated header. */
export default function SiteHeader() {
  const pathname = usePathname();
  const { lang } = useLanguage();
  const t = translations[lang];
  const [open, setOpen] = useState(false);
  const navRef = useNavIndicator<HTMLElement>();

  useEffect(() => {
    if (!open) return;
    const close = (event: KeyboardEvent) => { if (event.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [open]);

  return (
    <header className={`site-header ${open ? "is-open" : ""}`}>
      <Link className="site-brand" href="/" aria-label="Fence home"><span className="site-brand-mark" aria-hidden="true">F</span><span className="site-brand-name">Fence</span><small>preview</small></Link>
      <nav className="site-nav" aria-label="Primary navigation" ref={navRef}>
        {SITE_NAV.map((item) => (
          <Link key={item.href} href={item.href} aria-current={pathname === item.href ? "page" : undefined}>{t.nav[item.key]}</Link>
        ))}
        <span className="nav-indicator" aria-hidden="true" />
      </nav>
      <div className="site-actions">
        <Link className="site-signin" href="/login">{t.header.signIn}</Link>
        <Link className="site-signup" href="/register">{t.header.signUp}</Link>
        <button className="site-menu-toggle" type="button" aria-expanded={open} aria-controls="site-mobile-nav" onClick={() => setOpen((value) => !value)}>
          <span aria-hidden="true">{open ? "×" : "☰"}</span><span className="sr-only">Menu</span>
        </button>
      </div>
      <nav id="site-mobile-nav" className="site-mobile-nav" aria-label="Mobile navigation">
        {SITE_NAV.map((item) => (
          <Link key={item.href} href={item.href} aria-current={pathname === item.href ? "page" : undefined}>{t.nav[item.key]}</Link>
        ))}
        <Link href="/login">{t.header.signIn}</Link>
        <Link href="/register">{t.header.signUp}</Link>
      </nav>
    </header>
  );
}
