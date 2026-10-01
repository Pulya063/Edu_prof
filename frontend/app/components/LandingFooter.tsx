import { HeadlineLine } from "../hooks/useScrollMotion";
import { useLanguage, type Lang } from "../context/LanguageContext";
import { translations } from "../utils/translations";

const footerColumns = [
  {
    title: "Product",
    links: [
      { label: "University comparison" },
      { label: "Education ROI" },
      { label: "Career roadmap" },
      { label: "Scholarship matching" },
    ],
  },
  {
    title: "Discover",
    links: [
      { label: "How it works" },
      { label: "Decision examples" },
      { label: "Career guides" },
      { label: "FAQ" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "About Fence" },
      { label: "Pricing", href: "/plans" },
      { label: "Contact" },
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

function FooterLink({ label, href }: { label: string; href?: string }) {
  if (href === "/plans") return <a className="footer-link" href={href}>{label}</a>;
  return <span className="footer-link footer-link--inactive" aria-disabled="true">{label}<small>soon</small></span>;
}

export default function LandingFooter() {
  const { lang, setLang } = useLanguage();
  const backToTop = () => window.scrollTo({ top: 0, behavior: "smooth" });

  return (
    <footer className="fence-footer" id="footer" data-motion-section="true" data-header-theme="dark" aria-labelledby="footer-title">
      <span className="footer-texture" aria-hidden="true" />
      <div className="footer-boundary" aria-hidden="true" />
      <div className="footer-ready-wrap">
        <a className="footer-ready-card" href="/plans">
          <span><strong>See the plans.</strong><small>Preview simple pricing for clearer decisions.</small></span>
          <i className="footer-ready-orb" aria-hidden="true" />
          <b aria-hidden="true"><Arrow /></b>
        </a>
      </div>
      <div className="footer-shell">
        <section className="footer-brand" aria-labelledby="footer-title">
          <div className="footer-wordmark" aria-label="Fence"><i>F</i><strong>Fence</strong></div>
          <h2 id="footer-title"><HeadlineLine>A <span className="footer-oval">clearer</span> path</HeadlineLine><HeadlineLine>from study to <span className="footer-lime">career.</span></HeadlineLine></h2>
          <p>Compare the cost. Test the outcome. Plan the next move.</p>
        </section>
        <div className="footer-navigation" aria-label="Footer navigation">
          {footerColumns.map((column) => <nav className="footer-column" aria-labelledby={`footer-${column.title.toLowerCase()}`} key={column.title}><h3 id={`footer-${column.title.toLowerCase()}`}>{column.title}</h3><ul>{column.links.map((link) => <li key={link.label}><FooterLink {...link} /></li>)}</ul></nav>)}
          <nav className="footer-column" aria-labelledby="footer-connect"><h3 id="footer-connect">Connect</h3><ul>{["Instagram", "LinkedIn", "Email"].map((label) => <li key={label}><FooterLink label={label} /></li>)}</ul></nav>
        </div>
      </div>
      <div className="footer-legal"><p>© 2026 Fence. Education-to-career decision planning.</p><div className="footer-legal-actions">{["Privacy", "Terms", "Cookies"].map((label) => <span className="footer-link footer-link--inactive" aria-disabled="true" key={label}>{label}<small>draft</small></span>)}<label className="footer-language">Language: <select aria-label="Site language" value={lang} onChange={(event) => setLang(event.target.value as Lang)}>{(["en", "uk", "pl"] as const).map((code) => <option key={code} value={code}>{translations[lang].langLabels[code]}</option>)}</select></label><button className="footer-back-to-top" type="button" aria-label="Back to top" onClick={backToTop}><Arrow up /></button></div></div>
    </footer>
  );
}
