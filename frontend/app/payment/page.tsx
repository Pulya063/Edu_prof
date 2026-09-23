"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Check, LockKeyhole } from "lucide-react";
import "./payment.css";

const planNames: Record<string, string> = {
  pro: "Pro",
  business: "Business",
  enterprise: "Enterprise",
};

export default function PaymentPage() {
  const [plan, setPlan] = useState("business");
  const [cycle, setCycle] = useState("yearly");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setPlan(params.get("plan") ?? "business");
    setCycle(params.get("cycle") ?? "yearly");
  }, []);

  const planName = planNames[plan] ?? "Business";
  const price = plan === "pro" ? (cycle === "monthly" ? "$4.99" : "$3.99") : plan === "enterprise" ? (cycle === "monthly" ? "$39.99" : "$31.99") : (cycle === "monthly" ? "$9.99" : "$7.99");

  return (
    <main className="payment-page">
      <div className="payment-art" aria-hidden="true"><span /><span /><i /></div>
      <header className="payment-header">
        <Link href="/plans" className="payment-back"><ArrowLeft size={16} aria-hidden="true" /> Back to plans</Link>
        <span className="payment-brand"><b>F</b> Fence <small>secure checkout</small></span>
      </header>
      <section className="payment-shell" aria-labelledby="payment-title">
        <div className="payment-copy">
          <p className="payment-eyebrow">SECURE CHECKOUT</p>
          <h1 id="payment-title">One clear step<br /><em>from getting started.</em></h1>
          <p>Review your plan and continue to payment when everything looks right.</p>
          <div className="payment-trust"><LockKeyhole size={16} aria-hidden="true" /> Secure billing flow</div>
        </div>
        <aside className="payment-card">
          <div className="payment-card-top"><span>Selected plan</span><span className="payment-step">01 / 02</span></div>
          <h2>{planName}</h2>
          <p className="payment-cycle">{cycle === "monthly" ? "Monthly billing" : "Yearly billing"}</p>
          <div className="payment-price"><strong>{price}</strong><span>/ month</span></div>
          <ul><li><Check size={15} aria-hidden="true" /> Career ROI simulations</li><li><Check size={15} aria-hidden="true" /> Saved scenarios</li><li><Check size={15} aria-hidden="true" /> Personal roadmap</li></ul>
          <button type="button" className="payment-continue" disabled aria-disabled="true">Continue to payment <span aria-hidden="true">↗</span></button>
          <p className="payment-note">Payment integration is ready for the next step.</p>
        </aside>
      </section>
    </main>
  );
}
