"use client";

import { HeadlineLine } from "../hooks/useScrollMotion";

import Link from "next/link";
const supportEmail = process.env.NEXT_PUBLIC_FENCE_SUPPORT_EMAIL;

// Only pages that exist are linked; nothing in the footer is a placeholder.
const footerColumns = [
  {
    title: "Product",
    links: [
      { label: "Calculation", href: "/calculation" },
      { label: "Pricing", href: "/pricing" },
      { label: "Create account", href: "/register" },
      { label: "Sign in", href: "/login" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "About Fence", href: "/about" },
      { label: "Contact", href: "/contact" },
      ...(supportEmail ? [{ label: "Email", href: `mailto:${supportEmail}` }] : []),
    ],
  },
];

const legalLinks = [
  { label: "Privacy", href: "/legal/privacy" },
  { label: "Terms", href: "/legal/terms" },
  { label: "Cookies", href: "/legal/cookies" },
];

function Arrow({ up = false }: { up?: boolean }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" focusable="false">
      <path d={up ? "M12 19V5m-6 6 6-6 6 6" : "M5 12h14m-6-6 6 6-6 6"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function FooterLink({ label, href }: { label: string; href: string }) {
  return href.startsWith("/") ? <Link className="footer-link" href={href}>{label}</Link> : <a className="footer-link" href={href}>{label}</a>;
}

export default function LandingFooter() {
  const backToTop = () => window.scrollTo({ top: 0, behavior: "smooth" });

  return (
    <footer className="fence-footer" id="footer" data-motion-section="true" data-header-theme="dark" aria-labelledby="footer-title">
      <span className="footer-texture" aria-hidden="true" />
      <div className="footer-boundary" aria-hidden="true" />
      <div className="footer-ready-wrap">
        <Link className="footer-ready-card" href="/pricing">
          <span><strong>See the plans.</strong><small>Simple pricing, billed securely through Stripe.</small></span>
          <i className="footer-ready-orb" aria-hidden="true" />
          <b aria-hidden="true"><Arrow /></b>
        </Link>
      </div>
      <div className="footer-shell">
        <section className="footer-brand" aria-labelledby="footer-title">
          <div className="footer-wordmark" aria-label="Fence"><i>F</i><strong>Fence</strong></div>
          <h2 id="footer-title"><HeadlineLine>A <span className="footer-oval">clearer</span> path</HeadlineLine><HeadlineLine>from study to <span className="footer-lime">career.</span></HeadlineLine></h2>
          <p>Compare the cost. Test the outcome. Plan the next move.</p>
        </section>
        <div className="footer-navigation" aria-label="Footer navigation">
          {footerColumns.map((column) => <nav className="footer-column" aria-labelledby={`footer-${column.title.toLowerCase()}`} key={column.title}><h3 id={`footer-${column.title.toLowerCase()}`}>{column.title}</h3><ul>{column.links.map((link) => <li key={link.label}><FooterLink {...link} /></li>)}</ul></nav>)}
        </div>
      </div>
      <div className="footer-legal"><p>© 2026 Fence. Education-to-career decision planning.</p><div className="footer-legal-actions">{legalLinks.map((link) => <FooterLink key={link.href} {...link} />)}<button className="footer-back-to-top" type="button" aria-label="Back to top" onClick={backToTop}><Arrow up /></button></div></div>
    </footer>
  );
}
