"""Stripe Checkout payments.

Card data never reaches Fence: users pay on Stripe's hosted Checkout page. Prices are
resolved from server configuration (Stripe Price IDs in env), never from the client, and
a user's plan changes only after a signature-verified webhook confirms payment.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone

import stripe
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models import Payment, StripeEvent, User
from app.schemas import (
    CheckoutRequest,
    CheckoutResponse,
    PaymentPlanOption,
    PaymentPlansResponse,
    PaymentStatusResponse,
)

logger = logging.getLogger(__name__)

FREE_PLAN = "Free"
WEBHOOK_TOLERANCE_SECONDS = 300


@dataclass(frozen=True)
class PlanPrice:
    plan: str
    plan_name: str
    cycle: str
    # Charged amount per billing period in minor units; must match the Stripe Price.
    amount: int
    currency: str
    price_env: str

    @property
    def price_id(self) -> str:
        return os.getenv(self.price_env, "").strip()


# Display amounts mirror the Stripe Prices; the charge itself is always the Stripe Price.
PLAN_CATALOG: dict[tuple[str, str], PlanPrice] = {
    ("pro", "monthly"): PlanPrice("pro", "Pro", "monthly", 499, "usd", "STRIPE_PRICE_PRO_MONTHLY"),
    ("pro", "yearly"): PlanPrice("pro", "Pro", "yearly", 4788, "usd", "STRIPE_PRICE_PRO_YEARLY"),
    ("business", "monthly"): PlanPrice("business", "Plus", "monthly", 999, "usd", "STRIPE_PRICE_PLUS_MONTHLY"),
    ("business", "yearly"): PlanPrice("business", "Plus", "yearly", 9588, "usd", "STRIPE_PRICE_PLUS_YEARLY"),
    ("enterprise", "monthly"): PlanPrice("enterprise", "Teams", "monthly", 3999, "usd", "STRIPE_PRICE_TEAMS_MONTHLY"),
    ("enterprise", "yearly"): PlanPrice("enterprise", "Teams", "yearly", 38388, "usd", "STRIPE_PRICE_TEAMS_YEARLY"),
}

PLAN_NAMES = {price.plan: price.plan_name for price in PLAN_CATALOG.values()}


def stripe_secret_key() -> str:
    return os.getenv("STRIPE_SECRET_KEY", "").strip()


def stripe_webhook_secret() -> str:
    return os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()


def payments_configured() -> bool:
    return bool(stripe_secret_key())


def _frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:3221").rstrip("/")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PaymentService:
    def __init__(self, session: Session) -> None:
        self.session = session

    # --- catalog -----------------------------------------------------------------

    def list_plans(self, user: User | None) -> PaymentPlansResponse:
        configured = payments_configured()
        publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY", "").strip() or None
        return PaymentPlansResponse(
            configured=configured,
            publishable_key=publishable_key if configured else None,
            current_plan=user.plan if user else None,
            options=[
                PaymentPlanOption(
                    plan=price.plan,
                    plan_name=price.plan_name,
                    cycle=price.cycle,
                    amount=price.amount,
                    currency=price.currency,
                    available=configured and bool(price.price_id),
                )
                for price in PLAN_CATALOG.values()
            ],
        )

    # --- checkout ----------------------------------------------------------------

    def create_checkout(self, user: User, request: CheckoutRequest) -> CheckoutResponse:
        if not payments_configured():
            raise AppError("Payments are not configured yet", status_code=503)
        price = PLAN_CATALOG[(request.plan, request.cycle)]
        if not price.price_id:
            raise AppError("This plan cannot be purchased yet", status_code=503)

        frontend = _frontend_url()
        metadata = {"fence_user_id": str(user.id), "plan": price.plan, "cycle": price.cycle}
        params: dict[str, object] = {
            "mode": "subscription",
            "line_items": [{"price": price.price_id, "quantity": 1}],
            "client_reference_id": str(user.id),
            "metadata": metadata,
            "subscription_data": {"metadata": metadata},
            "success_url": f"{frontend}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{frontend}/payment/cancel?plan={price.plan}&cycle={price.cycle}",
            "allow_promotion_codes": True,
        }
        customer_id = self._latest_customer_id(user.id)
        if customer_id:
            params["customer"] = customer_id

        try:
            checkout = self._create_stripe_session(params)
        except stripe.StripeError as error:
            logger.warning("Stripe checkout creation failed for user_id=%s: %s", user.id, error.__class__.__name__)
            raise AppError("Could not open checkout. Try again later.", status_code=502) from error

        self.session.add(
            Payment(
                user_id=user.id,
                checkout_session_id=checkout.id,
                stripe_customer_id=customer_id,
                plan=price.plan,
                billing_cycle=price.cycle,
                status="pending",
                amount_expected=price.amount,
                currency=price.currency,
            )
        )
        self.session.commit()
        logger.info("Created checkout session for user_id=%s plan=%s cycle=%s", user.id, price.plan, price.cycle)
        return CheckoutResponse(checkout_url=checkout.url, session_id=checkout.id)

    def _create_stripe_session(self, params: dict[str, object]):
        client = stripe.StripeClient(stripe_secret_key())
        return client.v1.checkout.sessions.create(params=params)

    def _latest_customer_id(self, user_id: int) -> str | None:
        return self.session.scalar(
            select(Payment.stripe_customer_id)
            .where(Payment.user_id == user_id, Payment.stripe_customer_id.is_not(None))
            .order_by(Payment.created_at.desc(), Payment.id.desc())
            .limit(1)
        )

    # --- status ------------------------------------------------------------------

    def get_status(self, user: User, session_id: str) -> PaymentStatusResponse:
        payment = self.session.scalar(
            select(Payment).where(Payment.checkout_session_id == session_id, Payment.user_id == user.id)
        )
        if payment is None:
            raise AppError("Payment not found", status_code=404)
        return PaymentStatusResponse(
            session_id=payment.checkout_session_id,
            plan=payment.plan,
            plan_name=PLAN_NAMES.get(payment.plan, payment.plan),
            billing_cycle=payment.billing_cycle,
            status=payment.status,
            amount_expected=payment.amount_expected,
            amount_total=payment.amount_total,
            currency=payment.currency,
            paid_at=payment.paid_at,
            created_at=payment.created_at,
            current_plan=user.plan,
        )

    # --- webhook -----------------------------------------------------------------

    def handle_webhook(self, payload: bytes, signature: str | None) -> str:
        """Verify, deduplicate and apply a Stripe event. Returns a short outcome label."""
        secret = stripe_webhook_secret()
        if not secret:
            raise AppError("Webhook is not configured", status_code=503)
        if not signature:
            raise AppError("Stripe signature is missing", status_code=400)

        text = payload.decode("utf-8")
        try:
            stripe.WebhookSignature.verify_header(text, signature, secret, WEBHOOK_TOLERANCE_SECONDS)
        except stripe.SignatureVerificationError as error:
            logger.warning("Rejected Stripe webhook with invalid signature")
            raise AppError("Stripe signature is invalid", status_code=400) from error

        try:
            event = json.loads(text)
            event_id = str(event["id"])
            event_type = str(event["type"])
            data_object = event["data"]["object"]
        except (ValueError, KeyError, TypeError) as error:
            raise AppError("Invalid Stripe event", status_code=400) from error

        if self.session.get(StripeEvent, event_id) is not None:
            logger.info("Skipping duplicate Stripe event %s", event_id)
            return "duplicate"

        self.session.add(StripeEvent(event_id=event_id, event_type=event_type))
        handler = self._HANDLERS.get(event_type)
        outcome = handler(self, data_object) if handler is not None else "ignored"
        try:
            self.session.commit()
        except IntegrityError:
            # A concurrent delivery of the same event won the race.
            self.session.rollback()
            return "duplicate"
        logger.info("Processed Stripe event %s type=%s outcome=%s", event_id, event_type, outcome)
        return outcome

    # --- identity checks ---------------------------------------------------------
    #
    # Each checkout session carries our internal user id twice (client_reference_id and
    # metadata.fence_user_id) plus plan/cycle in metadata. An event is applied only when its
    # session id maps to our payment row AND every one of these echoes back what we stored.

    def _resolve_session_payment(self, data_object: dict) -> Payment | None:
        session_id = data_object.get("id")
        if not session_id:
            logger.error("Stripe checkout event without a session id")
            return None
        payment = self.session.scalar(select(Payment).where(Payment.checkout_session_id == str(session_id)))
        if payment is None:
            payment = self._recover_payment(data_object)
            if payment is None:
                return None
        if not self._identity_matches(payment, data_object):
            return None
        return payment

    def _identity_matches(self, payment: Payment, data_object: dict) -> bool:
        metadata = data_object.get("metadata") or {}
        expected = {
            "client_reference_id": str(payment.user_id),
            "metadata.fence_user_id": str(payment.user_id),
            "metadata.plan": payment.plan,
            "metadata.cycle": payment.billing_cycle,
        }
        received = {
            "client_reference_id": data_object.get("client_reference_id"),
            "metadata.fence_user_id": metadata.get("fence_user_id"),
            "metadata.plan": metadata.get("plan"),
            "metadata.cycle": metadata.get("cycle"),
        }
        mismatched = [key for key, value in expected.items() if received[key] is None or str(received[key]) != value]
        customer = data_object.get("customer")
        if payment.stripe_customer_id and customer and customer != payment.stripe_customer_id:
            mismatched.append("customer")
        if mismatched:
            logger.error("Stripe identity mismatch for payment_id=%s fields=%s", payment.id, ",".join(mismatched))
            return False
        return True

    def _recover_payment(self, data_object: dict) -> Payment | None:
        """Rebuild a payment row lost after Stripe created the session (e.g. our commit failed).

        Only signed events whose two user-id copies agree, point to an existing user and name a
        catalog plan are recovered; anything else is rejected.
        """
        metadata = data_object.get("metadata") or {}
        reference = str(data_object.get("client_reference_id") or "")
        if not reference.isdigit() or reference != str(metadata.get("fence_user_id")):
            logger.error("Stripe session without a payment record and without consistent user ids")
            return None
        price = PLAN_CATALOG.get((str(metadata.get("plan")), str(metadata.get("cycle"))))
        user = self.session.get(User, int(reference))
        if price is None or user is None:
            logger.error("Stripe session without a payment record references unknown user or plan")
            return None
        payment = Payment(
            user_id=user.id,
            checkout_session_id=str(data_object["id"]),
            plan=price.plan,
            billing_cycle=price.cycle,
            status="pending",
            amount_expected=price.amount,
            currency=price.currency,
        )
        self.session.add(payment)
        self.session.flush()
        logger.warning("Recovered missing payment record payment_id=%s from Stripe session", payment.id)
        return payment

    # --- event handlers ----------------------------------------------------------

    def _on_checkout_completed(self, data_object: dict) -> str:
        payment = self._resolve_session_payment(data_object)
        if payment is None:
            return "rejected"
        payment.stripe_customer_id = data_object.get("customer") or payment.stripe_customer_id
        payment.stripe_subscription_id = data_object.get("subscription") or payment.stripe_subscription_id
        payment.amount_total = data_object.get("amount_total")
        if data_object.get("currency"):
            payment.currency = str(data_object["currency"]).lower()
        if data_object.get("payment_status") in {"paid", "no_payment_required"}:
            self._mark_paid(payment)
        return "processed"

    def _on_async_payment_succeeded(self, data_object: dict) -> str:
        payment = self._resolve_session_payment(data_object)
        if payment is None:
            return "rejected"
        self._mark_paid(payment)
        return "processed"

    def _on_async_payment_failed(self, data_object: dict) -> str:
        payment = self._resolve_session_payment(data_object)
        if payment is None:
            return "rejected"
        if payment.status == "pending":
            payment.status = "failed"
        return "processed"

    def _on_session_expired(self, data_object: dict) -> str:
        payment = self._resolve_session_payment(data_object)
        if payment is None:
            return "rejected"
        if payment.status == "pending":
            payment.status = "expired"
        return "processed"

    def _on_subscription_deleted(self, data_object: dict) -> str:
        payment = self.session.scalar(
            select(Payment)
            .where(Payment.stripe_subscription_id == str(data_object.get("id")), Payment.status == "paid")
            .order_by(Payment.paid_at.desc())
            .limit(1)
        )
        if payment is None:
            return "ignored"
        # subscription_data.metadata carries the same user id we set at checkout.
        owner = (data_object.get("metadata") or {}).get("fence_user_id")
        customer = data_object.get("customer")
        if str(owner) != str(payment.user_id) or (
            payment.stripe_customer_id and customer and customer != payment.stripe_customer_id
        ):
            logger.error("Stripe subscription identity mismatch for payment_id=%s", payment.id)
            return "rejected"
        payment.status = "canceled"
        payment.canceled_at = _utcnow()
        user = self.session.get(User, payment.user_id)
        if user is not None and user.plan == PLAN_NAMES.get(payment.plan):
            user.plan = FREE_PLAN
        return "processed"

    def _mark_paid(self, payment: Payment) -> None:
        if payment.status == "paid":
            return
        payment.status = "paid"
        payment.paid_at = _utcnow()
        user = self.session.get(User, payment.user_id)
        if user is not None:
            user.plan = PLAN_NAMES[payment.plan]

    _HANDLERS = {
        "checkout.session.completed": _on_checkout_completed,
        "checkout.session.async_payment_succeeded": _on_async_payment_succeeded,
        "checkout.session.async_payment_failed": _on_async_payment_failed,
        "checkout.session.expired": _on_session_expired,
        "customer.subscription.deleted": _on_subscription_deleted,
    }
