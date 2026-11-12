"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { ApiRequestError } from "@/lib/api/client";
import { formatMoney, getPaymentStatus, type PaymentStatusResponse } from "@/lib/api/payments";
import "../../styles/payment.css";

// Stripe redirects here before the webhook may have arrived, so poll our API for a short while.
const POLL_INTERVAL_MS = 2000;
const MAX_POLLS = 15;

export default function PaymentSuccessPage() {
  const [payment, setPayment] = useState<PaymentStatusResponse | null>(null);
  const [error, setError] = useState("");
  const [timedOut, setTimedOut] = useState(false);

  useEffect(() => {
    const sessionId = new URLSearchParams(window.location.search).get("session_id");
    if (!sessionId) { setError("Missing checkout session reference."); return; }
    let cancelled = false;
    let attempts = 0;
    let timer: ReturnType<typeof setTimeout>;

    const poll = async () => {
      attempts += 1;
      try {
        const status = await getPaymentStatus(sessionId);
        if (cancelled) return;
        setPayment(status);
        if (status.status !== "pending") return;
      } catch (requestError) {
        if (cancelled) return;
        if (requestError instanceof ApiRequestError && requestError.status === 401) {
          window.location.assign(`/login?next=${encodeURIComponent(`/payment/success?session_id=${sessionId}`)}`);
          return;
        }
        setError(requestError instanceof Error ? requestError.message : "Could not load payment status.");
        return;
      }
      if (attempts >= MAX_POLLS) { setTimedOut(true); return; }
      timer = setTimeout(poll, POLL_INTERVAL_MS);
    };
    poll();
    return () => { cancelled = true; clearTimeout(timer); };
  }, []);

  const status = payment?.status;
  const title = error ? "We could not check this payment." : status === "paid" ? "Payment confirmed." : status && status !== "pending" ? "Payment not completed." : "Confirming payment…";
  const lead = error
    ? error
    : status === "paid"
      ? `Your ${payment?.plan_name} plan is active.`
      : status && status !== "pending"
        ? "Stripe did not confirm this payment. You have not been upgraded."
        : timedOut
          ? "Stripe has not confirmed the payment yet. It can take a minute — refresh this page or check your plan in settings later."
          : "Waiting for Stripe to confirm. Your plan activates only after confirmation.";

  return (
    <main className="payment-page">
      <div className="payment-art" aria-hidden="true"><span /><span /><i /></div>
      <header className="payment-header">
        <Link href="/pricing" className="payment-back"><ArrowLeft size={16} aria-hidden="true" /> Back to plans</Link>
        <span className="payment-brand"><b>F</b> Fence <small>checkout</small></span>
      </header>
      <section className="payment-shell" aria-labelledby="payment-title">
        <div className="payment-copy" aria-live="polite">
          <p className="payment-eyebrow">CHECKOUT / STEP 02 OF 02</p>
          <h1 id="payment-title">{title}</h1>
          <p>{lead}</p>
        </div>
        <aside className="payment-card">
          <div className="payment-card-top"><span>Payment status</span><span className="payment-step">02 / 02</span></div>
          <h2>{payment?.plan_name ?? "—"}</h2>
          <div className="payment-status-row"><span>Status</span><strong>{status ?? (error ? "unknown" : "checking")}</strong></div>
          <div className="payment-status-row"><span>Billing</span><strong>{payment ? (payment.billing_cycle === "yearly" ? "Yearly" : "Monthly") : "—"}</strong></div>
          <div className="payment-status-row"><span>Amount</span><strong>{payment ? formatMoney(payment.amount_total ?? payment.amount_expected, payment.currency) : "—"}</strong></div>
          <div className="payment-status-row"><span>Current plan</span><strong>{payment?.current_plan ?? "—"}</strong></div>
          <div className="payment-result-actions">
            <Link href="/workspace/overview">Go to workspace</Link>
            {status && status !== "paid" && status !== "pending" ? <Link href="/payment">Try again</Link> : null}
          </div>
        </aside>
      </section>
    </main>
  );
}
