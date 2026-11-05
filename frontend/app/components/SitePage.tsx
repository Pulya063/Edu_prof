import type { ReactNode } from "react";
import SiteHeader from "./SiteHeader";
import LandingFooter from "./LandingFooter";
import "../styles/site-pages.css";
import "../styles/site-lively.css";

/** Shell for public sub-pages: shared header, editorial body, the landing footer. */
export default function SitePage({ kicker, title, lead, art, children }: { kicker: string; title: ReactNode; lead: ReactNode; art?: ReactNode; children: ReactNode }) {
  return (
    <div className="site-page">
      <SiteHeader />
      <main className="site-main">
        <section className={`site-hero ${art ? "site-hero--art" : ""}`}>
          <div className="site-hero-copy">
            <p className="site-kicker">{kicker}</p>
            <h1>{title}</h1>
            <p className="site-lead">{lead}</p>
          </div>
          {art}
        </section>
        {children}
      </main>
      <LandingFooter />
    </div>
  );
}
