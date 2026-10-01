"use client";

import { useState } from "react";
import { Check } from "lucide-react";
import "../styles/plans.css";

type BillingCycle = "monthly" | "yearly";
type Plan = {
  id: string;
  name: string;
  description: string;
  priceMonthly: string;
  priceYearly: string;
  featuresLabel: string;
  features: string[];
  badge?: string;
};

const plans: Plan[] = [
  { id: "pro", name: "Pro", description: "For one person comparing education and career paths", priceMonthly: "$4.99", priceYearly: "$3.99", featuresLabel: "PLANNED FEATURES", features: ["Education ROI scenarios", "Saved comparisons", "Personal career roadmap"] },
  { id: "business", name: "Plus", description: "For deeper comparisons across more options", priceMonthly: "$9.99", priceYearly: "$7.99", badge: "PREVIEW", featuresLabel: "EVERYTHING IN PRO, PLUS", features: ["Advanced scenario comparison", "Scholarship matching", "Skills-gap insights", "Extended roadmap planning"] },
  { id: "enterprise", name: "Teams", description: "For schools, advisors, and education teams", priceMonthly: "$39.99", priceYearly: "$31.99", featuresLabel: "EVERYTHING IN PLUS, PLUS", features: ["Shared scenario library", "Team workspaces", "Advisor-ready summaries"] },
];

export default function PlansPage() {
  const [cycle, setCycle] = useState<BillingCycle>("yearly");

  return <main className="plans-page">
    <header className="plans-header"><a href="/" className="plans-brand"><span>F</span> Fence <small>pricing preview</small></a><a href="/" className="plans-back">Back to overview <span aria-hidden="true">↗</span></a></header>
    <div className="plans-art" aria-hidden="true"><span className="plans-art-window plans-art-window--violet" /><span className="plans-art-window plans-art-window--lime" /><span className="plans-art-spot plans-art-spot--lime" /><span className="plans-art-spot plans-art-spot--violet" /><span className="plans-art-line plans-art-line--one" /><span className="plans-art-line plans-art-line--two" /></div>
    <section className="plans-hero" aria-labelledby="plans-title"><p className="plans-eyebrow">PRICING PREVIEW / BILLING NOT YET ACTIVE</p><h1 id="plans-title">Choose the depth<br /><em>your decision needs.</em></h1><p>Compare the planned tiers for education ROI, career scenarios, and roadmap support. Prices and billing terms remain provisional until launch.</p></section>

    <section className="plans-controls" aria-label="Plan controls"><div className="billing-toggle" role="group" aria-label="Billing cycle"><button type="button" className={cycle === "monthly" ? "is-active" : ""} onClick={() => setCycle("monthly")}>Monthly preview</button><button type="button" className={cycle === "yearly" ? "is-active" : ""} onClick={() => setCycle("yearly")}>Yearly preview <span>20% lower</span></button></div><span className="plans-controls-note">No checkout or charge is available</span></section>

    <section className="plans-grid" aria-label="Available plans">
      {plans.map((plan) => <article className={`plan-card ${plan.id === "business" ? "is-selected" : ""}`} key={plan.id}>
        <div className="plan-card-top"><div><p className="plan-name">{plan.name}</p>{plan.badge && <span className="plan-badge">{plan.badge}</span>}</div><span className="plan-card-index">0{plans.findIndex((item) => item.id === plan.id) + 1}</span></div>
        <p className="plan-description">{plan.description}</p><div className="plan-price"><strong>{cycle === "monthly" ? plan.priceMonthly : plan.priceYearly}</strong><span>/ month</span></div>{cycle === "yearly" && <small className="plan-billed">billed yearly</small>}
        <button className="plan-select" type="button" disabled aria-disabled="true">Enrollment coming soon <span aria-hidden="true">—</span></button>
        <div className="plan-rule" /><p className="plan-features-label">{plan.featuresLabel}</p><ul>{plan.features.map((feature) => <li key={feature}><Check size={15} aria-hidden="true" />{feature}</li>)}</ul>
      </article>)}
    </section>
  </main>;
}
