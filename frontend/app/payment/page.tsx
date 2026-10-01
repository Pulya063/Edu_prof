"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Check, LockKeyhole } from "lucide-react";
import "../styles/payment.css";

const planNames: Record<string, string> = {
  pro: "Pro",
  business: "Plus",
  enterprise: "Teams",
};

export default function PaymentPage() {
  const [plan, setPlan] = useState("business");
  const [cycle, setCycle] = useState("yearly");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setPlan(params.get("plan") ?? "business");
    setCycle(params.get("cycle") ?? "yearly");
  }, []);

  const planName = planNames[plan] ?? "Plus";
  const price = plan === "pro" ? (cycle === "monthly" ? "$4.99" : "$3.99") : plan === "enterprise" ? (cycle === "monthly" ? "$39.99" : "$31.99") : (cycle === "monthly" ? "$9.99" : "$7.99");

  return (
    <main className="payment-page">
      <div className="payment-art" aria-hidden="true"><span /><span /><i /></div>
      <header className="payment-header">
        <Link href="/plans" className="payment-back"><ArrowLeft size={16} aria-hidden="true" /> Back to plans</Link>
        <span className="payment-brand"><b>F</b> Fence <small>checkout preview</small></span>
      </header>
      <section className="payment-shell" aria-labelledby="payment-title">
        <div className="payment-copy">
          <p className="payment-eyebrow">CHECKOUT PREVIEW / NOT ACTIVE</p>
          <h1 id="payment-title">Review the plan.<br /><em>No charge will occur.</em></h1>
          <p>This page previews the future checkout summary. Payments, subscriptions, and account activation are not available yet.</p>
          <div className="payment-trust"><LockKeyhole size={16} aria-hidden="true" /> Billing integration pending</div>
        </div>
        <aside className="payment-card">
          <div className="payment-card-top"><span>Selected plan</span><span className="payment-step">01 / 02</span></div>
          <h2>{planName}</h2>
          <p className="payment-cycle">{cycle === "monthly" ? "Monthly billing" : "Yearly billing"}</p>
          <div className="payment-price"><strong>{price}</strong><span>/ month</span></div>
          <ul><li><Check size={15} aria-hidden="true" /> Career ROI simulations</li><li><Check size={15} aria-hidden="true" /> Saved scenarios</li><li><Check size={15} aria-hidden="true" /> Personal roadmap</li></ul>
          <button type="button" className="payment-continue" disabled aria-disabled="true">Checkout coming soon <span aria-hidden="true">—</span></button>
          <p className="payment-note">No payment details are collected on this preview.</p>
        </aside>
      </section>
    </main>
  );
}
