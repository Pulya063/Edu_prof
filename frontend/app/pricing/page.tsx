"use client";

import { useState } from "react";
import { Check } from "lucide-react";
import "../styles/plans.css";
import { PLANS as plans, PRICING_FAQ } from "./plans";

type BillingCycle = "monthly" | "yearly";


export default function PlansPage() {
  const [cycle, setCycle] = useState<BillingCycle>("yearly");

  return <main className="plans-page">
    <header className="plans-header"><a href="/" className="plans-brand"><span>F</span> Fence <small>pricing</small></a><a href="/" className="plans-back">Back to overview <span aria-hidden="true">↗</span></a></header>
    <div className="plans-art" aria-hidden="true"><span className="plans-art-window plans-art-window--violet" /><span className="plans-art-window plans-art-window--lime" /><span className="plans-art-spot plans-art-spot--lime" /><span className="plans-art-spot plans-art-spot--violet" /><span className="plans-art-line plans-art-line--one" /><span className="plans-art-line plans-art-line--two" /></div>
    <section className="plans-hero" aria-labelledby="plans-title"><p className="plans-eyebrow">PRICING / BILLED VIA STRIPE</p><h1 id="plans-title">Choose the depth<br /><em>your decision needs.</em></h1><p>Compare the planned tiers for education ROI, career scenarios, and roadmap support. Payment happens on Stripe&rsquo;s hosted checkout; your plan activates once Stripe confirms it.</p></section>

    <section className="plans-controls" aria-label="Plan controls"><div className="billing-toggle" role="group" aria-label="Billing cycle"><button type="button" className={cycle === "monthly" ? "is-active" : ""} onClick={() => setCycle("monthly")}>Monthly</button><button type="button" className={cycle === "yearly" ? "is-active" : ""} onClick={() => setCycle("yearly")}>Yearly <span>20% lower</span></button></div><span className="plans-controls-note">Secure checkout via Stripe</span></section>

    <section className="plans-grid" aria-label="Available plans">
      {plans.map((plan) => <article className={`plan-card ${plan.id === "business" ? "is-selected" : ""}`} key={plan.id}>
        <div className="plan-card-top"><div><p className="plan-name">{plan.name}</p>{plan.badge && <span className="plan-badge">{plan.badge}</span>}</div><span className="plan-card-index">0{plans.findIndex((item) => item.id === plan.id) + 1}</span></div>
        <p className="plan-description">{plan.description}</p><div className="plan-price"><strong>{cycle === "monthly" ? plan.priceMonthly : plan.priceYearly}</strong><span>/ month</span></div>{cycle === "yearly" && <small className="plan-billed">billed yearly</small>}
        <a className="plan-select" href={`/payment?plan=${plan.id}&cycle=${cycle}`}>Choose {plan.name} <span aria-hidden="true">→</span></a>
        <div className="plan-rule" /><p className="plan-features-label">{plan.featuresLabel}</p><ul>{plan.features.map((feature) => <li key={feature}><Check size={15} aria-hidden="true" />{feature}</li>)}</ul>
      </article>)}
    </section>
    <section className="plans-faq" aria-labelledby="plans-faq-title">
      <h2 id="plans-faq-title">Questions before you choose</h2>
      <div className="plans-faq-list">
        {PRICING_FAQ.map(([question, answer]) => <details className="plans-faq-item" key={question}><summary>{question}</summary><p>{answer}</p></details>)}
      </div>
    </section>
  </main>;
}
