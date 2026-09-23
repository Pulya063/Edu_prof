"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Check } from "lucide-react";
import "./plans.css";

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
  { id: "pro", name: "Pro", description: "For individuals making confident decisions", priceMonthly: "$4.99", priceYearly: "$3.99", featuresLabel: "CORE FEATURES", features: ["Career ROI simulations", "Saved scenarios", "Personal roadmap"] },
  { id: "business", name: "Business", description: "For deeper planning and more options", priceMonthly: "$9.99", priceYearly: "$7.99", badge: "POPULAR", featuresLabel: "EVERYTHING IN PRO, PLUS", features: ["Advanced comparisons", "Scholarship matching", "Priority support", "Extended roadmap insights"] },
  { id: "enterprise", name: "Enterprise", description: "For schools and organizations", priceMonthly: "$39.99", priceYearly: "$31.99", featuresLabel: "EVERYTHING IN BUSINESS, PLUS", features: ["Unlimited simulations", "Team workspaces", "Dedicated success support"] },
];

export default function PlansPage() {
  const [cycle, setCycle] = useState<BillingCycle>("yearly");
  const router = useRouter();
  const goToPayment = (plan: Plan) => {
    const params = new URLSearchParams({ plan: plan.id, cycle });
    router.push(`/payment?${params.toString()}`);
  };

  return <main className="plans-page">
    <header className="plans-header"><a href="/" className="plans-brand"><span>F</span> Fence <small>plans</small></a><a href="/" className="plans-back">Back to home <span aria-hidden="true">↗</span></a></header>
    <div className="plans-art" aria-hidden="true"><span className="plans-art-window plans-art-window--violet" /><span className="plans-art-window plans-art-window--lime" /><span className="plans-art-spot plans-art-spot--lime" /><span className="plans-art-spot plans-art-spot--violet" /><span className="plans-art-line plans-art-line--one" /><span className="plans-art-line plans-art-line--two" /></div>
    <section className="plans-hero" aria-labelledby="plans-title"><p className="plans-eyebrow">A PLAN FOR THE NEXT STEP</p><h1 id="plans-title">Choose the clarity<br /><em>that fits you.</em></h1><p>Start with the tools you need today. Change your plan as your decisions become bigger.</p></section>

    <section className="plans-controls" aria-label="Plan controls"><div className="billing-toggle" role="group" aria-label="Billing cycle"><button type="button" className={cycle === "monthly" ? "is-active" : ""} onClick={() => setCycle("monthly")}>Monthly</button><button type="button" className={cycle === "yearly" ? "is-active" : ""} onClick={() => setCycle("yearly")}>Yearly <span>Save 20%</span></button></div><span className="plans-controls-note">Simple pricing. Clear next steps.</span></section>

    <section className="plans-grid" aria-label="Available plans">
      {plans.map((plan) => <article className={`plan-card ${plan.id === "business" ? "is-selected" : ""}`} key={plan.id}>
        <div className="plan-card-top"><div><p className="plan-name">{plan.name}</p>{plan.badge && <span className="plan-badge">{plan.badge}</span>}</div><span className="plan-card-index">0{plans.findIndex((item) => item.id === plan.id) + 1}</span></div>
        <p className="plan-description">{plan.description}</p><div className="plan-price"><strong>{cycle === "monthly" ? plan.priceMonthly : plan.priceYearly}</strong><span>/ month</span></div>{cycle === "yearly" && <small className="plan-billed">billed yearly</small>}
        <button className="plan-select" type="button" onClick={() => goToPayment(plan)}>Choose {plan.name} <span aria-hidden="true">↗</span></button>
        <div className="plan-rule" /><p className="plan-features-label">{plan.featuresLabel}</p><ul>{plan.features.map((feature) => <li key={feature}><Check size={15} aria-hidden="true" />{feature}</li>)}</ul>
      </article>)}
    </section>
  </main>;
}
