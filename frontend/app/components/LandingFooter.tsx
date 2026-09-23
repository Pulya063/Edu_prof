import { HeadlineLine } from "./motion";

type Navigate = (target: string) => void;

const supportEmail = process.env.NEXT_PUBLIC_FENCE_SUPPORT_EMAIL;
const instagramUrl = process.env.NEXT_PUBLIC_FENCE_INSTAGRAM_URL;
const linkedinUrl = process.env.NEXT_PUBLIC_FENCE_LINKEDIN_URL;

const footerColumns = [
  {
    title: "Product",
    links: [
      { label: "Compare universities", target: "comparison" },
      { label: "Calculate ROI", target: "calculator" },
      { label: "Career roadmap", target: "roadmap" },
      { label: "Scholarships", target: "scholarships" },
    ],
  },
  {
    title: "Discover",
    links: [
      { label: "How it works", target: "roadmap" },
      { label: "Student stories", target: "testimonials" },
      { label: "Career guides", target: "roadmap" },
      { label: "FAQ", target: "final-decision" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "About Fence", target: "hero" },
      { label: "Pricing", href: "/plans" },
      { label: "Contact", href: "/contact" },
    ],
  },
] as const;

function Arrow({ up = false }: { up?: boolean }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" focusable="false">
      <path d={up ? "M12 19V5m-6 6 6-6 6 6" : "M5 12h14m-6-6 6 6-6 6"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function FooterLink({ label, target, href, onNavigate }: { label: string; target?: string; href?: string; onNavigate: Navigate }) {
  if (target) {
    return <a className="footer-link" href={`#${target}`} onClick={(event) => { event.preventDefault(); onNavigate(target); }}>{label}</a>;
  }
  return <a className="footer-link" href={href}>{label}</a>;
}

function ConfiguredExternalLink({ label, href, kind }: { label: string; href?: string; kind: "social" | "email" }) {
  if (href) return <a className="footer-link" href={href} target={kind === "social" ? "_blank" : undefined} rel={kind === "social" ? "noreferrer" : undefined}>{label}</a>;
  const configName = kind === "email" ? "NEXT_PUBLIC_FENCE_SUPPORT_EMAIL" : `NEXT_PUBLIC_FENCE_${label.toUpperCase()}_URL`;
  return <span className="footer-link footer-link--config" aria-label={`${label} is awaiting ${configName} configuration`} title={`Set ${configName} to enable this link`}>{label}</span>;
}

export default function LandingFooter({ onNavigate }: { onNavigate: Navigate }) {
  const backToTop = () => window.scrollTo({ top: 0, behavior: "smooth" });

  return (
    <footer className="fence-footer" id="footer" data-motion-section="true" data-header-theme="dark" aria-labelledby="footer-title">
      <span className="footer-texture" aria-hidden="true" />
      <div className="footer-boundary" aria-hidden="true" />
      <div className="footer-ready-wrap">
        <a className="footer-ready-card" href="#calculator" onClick={(event) => { event.preventDefault(); onNavigate("calculator"); }}>
          <span><strong>Ready to decide?</strong><small>Turn questions into a plan.</small></span>
          <i className="footer-ready-orb" aria-hidden="true" />
          <b aria-hidden="true"><Arrow /></b>
        </a>
      </div>
      <div className="footer-shell">
        <section className="footer-brand" aria-labelledby="footer-title">
          <a className="footer-wordmark" href="#hero" onClick={(event) => { event.preventDefault(); onNavigate("hero"); }} aria-label="Fence home"><i>F</i><strong>Fence</strong></a>
          <h2 id="footer-title"><HeadlineLine>A <span className="footer-oval">clearer</span> path</HeadlineLine><HeadlineLine>to a <span className="footer-lime">brighter</span> future.</HeadlineLine></h2>
          <p>Data today. Brighter tomorrows.</p>
        </section>
        <div className="footer-navigation" aria-label="Footer navigation">
          {footerColumns.map((column) => <nav className="footer-column" aria-labelledby={`footer-${column.title.toLowerCase()}`} key={column.title}><h3 id={`footer-${column.title.toLowerCase()}`}>{column.title}</h3><ul>{column.links.map((link) => <li key={link.label}><FooterLink {...link} onNavigate={onNavigate} /></li>)}</ul></nav>)}
          <nav className="footer-column" aria-labelledby="footer-connect"><h3 id="footer-connect">Connect</h3><ul><li><ConfiguredExternalLink label="Instagram" href={instagramUrl} kind="social" /></li><li><ConfiguredExternalLink label="LinkedIn" href={linkedinUrl} kind="social" /></li><li><ConfiguredExternalLink label="Email" href={supportEmail ? `mailto:${supportEmail}` : undefined} kind="email" /></li></ul></nav>
        </div>
      </div>
      <div className="footer-legal"><p>© 2026 Fence. Built for confident education decisions.</p><div className="footer-legal-actions"><a className="footer-link" href="/legal/privacy">Privacy</a><a className="footer-link" href="/legal/terms">Terms</a><a className="footer-link" href="/legal/cookies">Cookies</a><button className="footer-language" type="button" disabled aria-describedby="language-status">Language: English <span aria-hidden="true">▾</span></button><span className="sr-only" id="language-status">Language selection is not configured yet.</span><button className="footer-back-to-top" type="button" aria-label="Back to top" onClick={backToTop}><Arrow up /></button></div></div>
    </footer>
  );
}
