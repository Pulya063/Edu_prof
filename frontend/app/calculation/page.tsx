import type { Metadata } from "next";
import SitePage from "../components/SitePage";
import { SiteHeroArt } from "../components/SiteInteractive";
import TrialCalculator from "../components/TrialCalculator";

export const metadata: Metadata = {
  title: "How the Education ROI and Payback Calculation Works",
  description: "How Fence calculates education cost, opportunity cost, payback and ROI: deterministic formulas, stored inputs and labelled sources.",
  alternates: { canonical: "/calculation" },
};

const steps = [
  {
    title: "Direct cost",
    body: "Annual tuition × study years, plus mandatory fees, extra courses and any additional living cost. Scholarships and grants are subtracted; the total never drops below zero.",
    formula: "tuition × years + fees + extra + living − scholarships",
  },
  {
    title: "Opportunity cost",
    body: "The income you would have earned without studying, for the years you study and the share of work you give up, minus what you still earn while studying.",
    formula: "baseline salary × years × share given up − study income",
  },
  {
    title: "Outcome",
    body: "Your starting salary comes from a stored market snapshot for the role, country and seniority, or from your own estimate, which is then labelled as user-provided. Each year both salaries grow by their own growth rate.",
    formula: "salary(year) = start × (1 + growth)^(year − 1)",
  },
  {
    title: "Return",
    body: "Each year Fence adds the difference between the target salary and the baseline salary. Payback is the month this running total covers the investment. ROI compares the total gain over the horizon with the investment.",
    formula: "ROI = (cumulative gain − investment) ÷ investment",
  },
];

const guarantees = [
  ["Numbers come from code", "Every amount is computed by a deterministic engine with exact decimal arithmetic. AI can review a result and comment on risks, but it never produces a number."],
  ["Inputs are saved with the result", "Each calculation stores its inputs, the methodology version and the sources it used, so you can always see where a figure came from."],
  ["Weak assumptions are flagged", "If tuition, salary or growth has no medium- or high-confidence source, the result is marked “Review assumptions” rather than presented as fact."],
  ["Changes create revisions", "Editing a scenario creates a new revision. Earlier results stay as they were, so comparisons stay fair."],
];

export default function CalculationPage() {
  return (
    <SitePage
      kicker="Fence / calculation"
      title={<>How Fence turns a study plan into <span className="site-mark">a number.</span></>}
      lead="Four steps, the same for every scenario: what the education costs, what you give up while studying, what you are likely to earn after, and when it pays back. Try it below."
      art={<SiteHeroArt items={[["Direct cost", "tuition × years"], ["Given up", "salary while studying"], ["Payback", "month by month"]]} />}
    >
      <section className="site-section site-section--play" aria-labelledby="play-title">
        <h2 id="play-title" className="site-section-title">Try it on real salary data</h2>
        <TrialCalculator />
      </section>

      <section className="site-section" aria-labelledby="steps-title">
        <h2 id="steps-title" className="site-section-title">The model</h2>
        <ol className="site-steps">
          {steps.map((step, index) => (
            <li key={step.title} className="site-step">
              <span className="site-step-index">0{index + 1}</span>
              <h3>{step.title}</h3>
              <p>{step.body}</p>
              <code>{step.formula}</code>
            </li>
          ))}
        </ol>
      </section>

      <section className="site-section site-section--dark" aria-labelledby="trust-title">
        <h2 id="trust-title" className="site-section-title">What you can rely on</h2>
        <div className="site-grid">
          {guarantees.map(([title, body]) => (
            <article key={title} className="site-card">
              <h3>{title}</h3>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="site-section" aria-labelledby="limits-title">
        <h2 id="limits-title" className="site-section-title">What it is not</h2>
        <p className="site-prose">A Fence result is a planning estimate built from the data and assumptions you can see. It is not a promise of a salary or a job, and it is not financial advice. Where Fence has no verified record for your university or role, it asks you for the figure instead of guessing.</p>
      </section>

      <section className="site-cta" aria-labelledby="cta-title">
        <h2 id="cta-title">Run it on your own plan.</h2>
        <div className="site-cta-actions">
          <a className="site-button site-button--lime" href="/try">Calculate my plan <span aria-hidden="true">→</span></a>
          <a className="site-button site-button--ghost" href="/pricing">See pricing</a>
        </div>
      </section>
    </SitePage>
  );
}
