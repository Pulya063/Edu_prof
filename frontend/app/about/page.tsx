import type { Metadata } from "next";
import SitePage from "../components/SitePage";
import { ProductTabs, SiteHeroArt } from "../components/SiteInteractive";

export const metadata: Metadata = {
  title: "About — Education Cost and Career Decisions",
  description: "Fence helps students and career changers compare the cost and likely return of an education path before they commit.",
  alternates: { canonical: "/about" },
};

const principles = [
  ["Show the full cost", "Tuition is only part of the price. Fence puts the income you give up while studying next to it, because that is often the larger number."],
  ["No invented numbers", "Salaries and tuition come from stored sources or from you, and are labelled either way. AI helps explain and plan; it never sets a figure."],
  ["Honest when data is missing", "If we have no verified record, Fence says so and asks for your figure. An empty state is better than a confident guess."],
  ["Plans, not promises", "A forecast is a way to compare options and plan next steps. Outcomes depend on many things a model cannot see."],
];


export default function AboutPage() {
  return (
    <SitePage
      kicker="Fence / about"
      title={<>Clearer decisions between <span className="site-mark">study and career.</span></>}
      lead="A degree is one of the biggest purchases a family makes, and most people buy it on reputation. Fence shows what a path really costs, when it pays back, and what to do next."
      art={<SiteHeroArt items={[["Built for", "students & parents"], ["Numbers", "from code, not AI"], ["Markets", "Poland · Ukraine"]]} />}
    >
      <section className="site-section" aria-labelledby="principles-title">
        <h2 id="principles-title" className="site-section-title">How we work</h2>
        <div className="site-grid">
          {principles.map(([title, body], index) => (
            <article key={title} className={`site-card ${index === 0 ? "site-card--lime" : ""}`}>
              <h3>{title}</h3>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="site-section site-section--dark" aria-labelledby="product-title">
        <h2 id="product-title" className="site-section-title">What Fence does</h2>
        <ProductTabs />
      </section>

      <section className="site-section" aria-labelledby="status-title">
        <h2 id="status-title" className="site-section-title">Where we are</h2>
        <p className="site-prose">Fence is in active development. Tuition and salary coverage is still growing, so for some universities and roles Fence will ask for your own figures. Questions, corrections and ideas are welcome on the <a href="/contact">contact page</a>.</p>
      </section>

      <section className="site-cta" aria-labelledby="cta-title">
        <h2 id="cta-title">Your first scenario is <span className="site-mark">one click away.</span></h2>
        <div className="site-cta-actions">
          <a className="site-button site-button--lime" href="/try">Try a calculation <span aria-hidden="true">→</span></a>
          <a className="site-button site-button--ghost" href="/calculation">How it is calculated</a>
        </div>
      </section>
    </SitePage>
  );
}
