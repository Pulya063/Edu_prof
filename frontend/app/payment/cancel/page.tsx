"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { isPlanId } from "@/lib/api/payments";
import "../../styles/payment.css";

export default function PaymentCancelPage() {
  const [retryHref, setRetryHref] = useState("/payment");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const plan = params.get("plan");
    const cycle = params.get("cycle") === "monthly" ? "monthly" : "yearly";
    if (isPlanId(plan)) setRetryHref(`/payment?plan=${plan}&cycle=${cycle}`);
  }, []);

  return (
    <main className="payment-page">
      <div className="payment-art" aria-hidden="true"><span /><span /><i /></div>
      <header className="payment-header">
        <Link href="/pricing" className="payment-back"><ArrowLeft size={16} aria-hidden="true" /> Back to plans</Link>
        <span className="payment-brand"><b>F</b> Fence <small>checkout</small></span>
      </header>
      <section className="payment-shell" aria-labelledby="payment-title">
        <div className="payment-copy">
          <p className="payment-eyebrow">CHECKOUT / CANCELLED</p>
          <h1 id="payment-title">Checkout cancelled.<br /><em>No charge.</em></h1>
          <p>You left Stripe before paying. Your plan has not changed.</p>
        </div>
        <aside className="payment-card">
          <div className="payment-card-top"><span>Nothing was charged</span><span className="payment-step">— / 02</span></div>
          <h2>Still deciding?</h2>
          <p className="payment-cycle">You can return to checkout or keep using your current plan.</p>
          <div className="payment-result-actions">
            <Link href={retryHref}>Return to checkout</Link>
            <Link href="/workspace/overview">Go to workspace</Link>
          </div>
        </aside>
      </section>
    </main>
  );
}
