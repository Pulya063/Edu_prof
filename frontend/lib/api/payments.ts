import { apiRequest } from "./client";

import type {
  CheckoutResponse,
  PaymentPlanOption as GeneratedPaymentPlanOption,
  PaymentPlansResponse,
  PaymentStatusResponse,
} from "./generated";

// Shapes come from app/schemas.py via generated.ts. Amounts are integers in minor units (cents).
export type PaymentPlanId = GeneratedPaymentPlanOption["plan"];
export type BillingCycle = GeneratedPaymentPlanOption["cycle"];
export type PaymentStatus = PaymentStatusResponse["status"];
export type PaymentPlanOption = GeneratedPaymentPlanOption;
export type PaymentPlans = PaymentPlansResponse;
export type CheckoutSession = CheckoutResponse;
export type { PaymentStatusResponse };

export const getPaymentPlans = () =>
  apiRequest<PaymentPlans>("/api/payments/plans", { fallbackMessage: "Could not load plans." });

export const createCheckout = (plan: PaymentPlanId, cycle: BillingCycle) =>
  apiRequest<CheckoutSession>("/api/payments/checkout", {
    method: "POST",
    body: JSON.stringify({ plan, cycle }),
    authenticated: true,
    fallbackMessage: "Could not open checkout.",
  });

export const getPaymentStatus = (sessionId: string) =>
  apiRequest<PaymentStatusResponse>(`/api/payments/sessions/${encodeURIComponent(sessionId)}`, {
    authenticated: true,
    fallbackMessage: "Could not load payment status.",
  });

export function formatMoney(amount: number, currency: string): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: currency.toUpperCase() }).format(amount / 100);
}

export function isPlanId(value: string | null): value is PaymentPlanId {
  return value === "pro" || value === "business" || value === "enterprise";
}
