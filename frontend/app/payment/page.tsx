"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Check, LockKeyhole } from "lucide-react";
import { ApiRequestError } from "@/lib/api/client";
import {
  createCheckout,
  formatMoney,
  getPaymentPlans,
  isPlanId,
  type BillingCycle,
  type PaymentPlanId,
  type PaymentPlans,
} from "@/lib/api/payments";
import "../styles/payment.css";

const planOrder: PaymentPlanId[] = ["pro", "business", "enterprise"];
const planFeatures: Record<PaymentPlanId, string[]> = {
  pro: ["30 career ROI calculations", "Saved scenarios", "AI review of projections"],
  business: ["100 career ROI calculations", "Advanced scenario comparison", "AI review of projections"],
  enterprise: ["Unlimited calculations", "Shared scenario library", "AI review of projections"],
};

export default function PaymentPage() {
  const [plan, setPlan] = useState<PaymentPlanId>("business");
  const [cycle, setCycle] = useState<BillingCycle>("yearly");
  const [catalog, setCatalog] = useState<PaymentPlans | null>(null);
  const [loadError, setLoadError] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const requestedPlan = params.get("plan");
    if (isPlanId(requestedPlan)) setPlan(requestedPlan);
    if (params.get("cycle") === "monthly") setCycle("monthly");
    getPaymentPlans().then(setCatalog).catch((error: Error) => setLoadError(error.message));
  }, []);

  const option = catalog?.options.find((item) => item.plan === plan && item.cycle === cycle);
  const planName = option?.plan_name ?? { pro: "Pro", business: "Plus", enterprise: "Teams" }[plan];
  const monthlyEquivalent = option ? formatMoney(cycle === "yearly" ? Math.round(option.amount / 12) : option.amount, option.currency) : "—";
  const isCurrentPlan = Boolean(catalog?.current_plan && catalog.current_plan === planName);
  const canCheckout = Boolean(catalog?.configured && option?.available && !isCurrentPlan && !submitting);

  let buttonLabel = "Continue to secure checkout";
  let note = "You will pay on Stripe's hosted page. Fence never sees your card details.";
  if (!catalog && !loadError) buttonLabel = "Loading plans…";
  else if (loadError) { buttonLabel = "Checkout unavailable"; note = loadError; }
  else if (!catalog?.configured) { buttonLabel = "Checkout not configured yet"; note = "Payments are not connected on this environment yet. No charge can occur."; }
  else if (!option?.available) { buttonLabel = "This plan is not on sale yet"; note = "Pick another plan or billing cycle."; }
  else if (isCurrentPlan) { buttonLabel = "This is your current plan"; note = "Your account already has this plan."; }
  else if (submitting) buttonLabel = "Opening Stripe…";

  async function startCheckout() {
    setSubmitError("");
    setSubmitting(true);
    try {
      const session = await createCheckout(plan, cycle);
      window.location.assign(session.checkout_url);
    } catch (error) {
      setSubmitting(false);
      if (error instanceof ApiRequestError && error.status === 401) {
        window.location.assign(`/login?next=${encodeURIComponent(`/payment?plan=${plan}&cycle=${cycle}`)}`);
        return;
      }
      setSubmitError(error instanceof Error ? error.message : "Could not open checkout.");
    }
  }

  return (
    <main className="payment-page">
      <div className="payment-art" aria-hidden="true"><span /><span /><i /></div>
      <header className="payment-header">
        <Link href="/pricing" className="payment-back"><ArrowLeft size={16} aria-hidden="true" /> Back to plans</Link>
        <span className="payment-brand"><b>F</b> Fence <small>checkout</small></span>
      </header>
      <section className="payment-shell" aria-labelledby="payment-title">
        <div className="payment-copy">
          <p className="payment-eyebrow">CHECKOUT / STEP 01 OF 02</p>
          <h1 id="payment-title">Review the plan.<br /><em>Pay on Stripe.</em></h1>
          <p>Choose a plan and billing cycle. Your plan activates as soon as Stripe confirms the payment — not before.</p>
          <div className="payment-trust"><LockKeyhole size={16} aria-hidden="true" /> Hosted Stripe Checkout · cancel any time</div>
        </div>
        <aside className="payment-card">
          <div className="payment-card-top"><span>Selected plan</span><span className="payment-step">01 / 02</span></div>
          <div className="payment-segments" role="radiogroup" aria-label="Plan">
            {planOrder.map((id) => (
              <button key={id} type="button" role="radio" aria-checked={plan === id} className={plan === id ? "is-active" : ""} onClick={() => setPlan(id)}>
                {catalog?.options.find((item) => item.plan === id)?.plan_name ?? { pro: "Pro", business: "Plus", enterprise: "Teams" }[id]}
              </button>
            ))}
          </div>
          <h2>{planName}</h2>
          <div className="payment-segments payment-segments--cycle" role="radiogroup" aria-label="Billing cycle">
            {(["monthly", "yearly"] as BillingCycle[]).map((value) => (
              <button key={value} type="button" role="radio" aria-checked={cycle === value} className={cycle === value ? "is-active" : ""} onClick={() => setCycle(value)}>
                {value === "monthly" ? "Monthly" : "Yearly · 20% lower"}
              </button>
            ))}
          </div>
          <div className="payment-price"><strong>{monthlyEquivalent}</strong><span>/ month</span></div>
          <p className="payment-cycle">{option ? (cycle === "yearly" ? `Billed ${formatMoney(option.amount, option.currency)} yearly` : "Billed monthly") : " "}</p>
          <ul>{planFeatures[plan].map((feature) => <li key={feature}><Check size={15} aria-hidden="true" /> {feature}</li>)}</ul>
          <button type="button" className="payment-continue" disabled={!canCheckout} aria-disabled={!canCheckout} onClick={startCheckout}>
            {buttonLabel} <span aria-hidden="true">{canCheckout ? "→" : "—"}</span>
          </button>
          {submitError ? <p className="payment-error" role="alert">{submitError}</p> : <p className="payment-note">{note}</p>}
        </aside>
      </section>
    </main>
  );
}
