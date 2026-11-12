import hashlib
import hmac
import json
import time
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import select

from app.core.database import db
from app.models import Payment, StripeEvent, User

WEBHOOK_SECRET = "whsec_test_secret"


def _fake_redis():
    store = {}
    client = MagicMock()
    client.setex.side_effect = lambda key, ttl, value: store.__setitem__(key, value)
    client.get.side_effect = store.get
    client.getdel.side_effect = lambda key: store.pop(key, None)
    client.delete.side_effect = lambda key: store.pop(key, None)
    return client


@pytest.fixture
def stripe_env(monkeypatch):
    monkeypatch.setattr("app.core.redis_client.get_redis", lambda: _fake_redis())
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_dummy")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)
    monkeypatch.setenv("STRIPE_PRICE_PRO_MONTHLY", "price_pro_monthly")
    created = []

    def fake_create(self, params):
        created.append(params)
        return SimpleNamespace(id=f"cs_test_{len(created)}", url="https://checkout.stripe.com/c/pay/test")

    monkeypatch.setattr("app.services.payment_service.PaymentService._create_stripe_session", fake_create)
    return created


def _login(client):
    response = client.post("/api/auth/register", json={"email": "payer@example.com", "password": "Passw0rd!"})
    assert response.status_code == 201
    return {"X-CSRF-Token": client.get_cookie("csrf_token").value}


def _sign(payload: str, secret: str = WEBHOOK_SECRET, timestamp: int | None = None) -> str:
    timestamp = timestamp or int(time.time())
    signature = hmac.new(secret.encode(), f"{timestamp}.{payload}".encode(), hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"


def _session_object(session_id: str, user_id: int, **overrides) -> dict:
    session = {
        "id": session_id,
        "client_reference_id": str(user_id),
        "metadata": {"fence_user_id": str(user_id), "plan": "pro", "cycle": "monthly"},
        "customer": "cus_123",
        "subscription": "sub_123",
        "payment_status": "paid",
        "amount_total": 499,
        "currency": "usd",
    }
    session.update(overrides)
    return session


def _completed_event(session_id: str, user_id: int, event_id: str = "evt_1", **overrides) -> str:
    return json.dumps({
        "id": event_id,
        "type": "checkout.session.completed",
        "data": {"object": _session_object(session_id, user_id, **overrides)},
    })


def _start_checkout(client, headers) -> str:
    response = client.post("/api/payments/checkout", json={"plan": "pro", "cycle": "monthly"}, headers=headers)
    assert response.status_code == 201
    return response.get_json()["session_id"]


def _post_webhook(client, payload: str, signature: str | None):
    headers = {"Content-Type": "application/json"}
    if signature is not None:
        headers["Stripe-Signature"] = signature
    return client.post("/api/payments/webhook", data=payload, headers=headers)


def _user(app) -> User:
    return db.session.execute(select(User).where(User.email == "payer@example.com")).scalar_one()


def test_plans_report_unconfigured_state_without_keys(client, monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    response = client.get("/api/payments/plans")
    assert response.status_code == 200
    body = response.get_json()
    assert body["configured"] is False
    assert all(option["available"] is False for option in body["options"])


def test_checkout_without_keys_returns_503(client, monkeypatch):
    monkeypatch.setattr("app.core.redis_client.get_redis", lambda: _fake_redis())
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    headers = _login(client)
    response = client.post("/api/payments/checkout", json={"plan": "pro", "cycle": "monthly"}, headers=headers)
    assert response.status_code == 503


def test_checkout_ignores_client_amount_and_uses_server_price(client, app, stripe_env):
    headers = _login(client)
    response = client.post(
        "/api/payments/checkout",
        json={"plan": "pro", "cycle": "monthly", "amount": 1, "price": "price_attacker", "currency": "jpy"},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.get_json()["checkout_url"].startswith("https://checkout.stripe.com/")

    params = stripe_env[0]
    assert params["line_items"] == [{"price": "price_pro_monthly", "quantity": 1}]
    assert "amount" not in json.dumps(params)
    user = _user(app)
    assert params["client_reference_id"] == str(user.id)
    assert "email" not in json.dumps(params["metadata"])

    payment = db.session.execute(select(Payment)).scalar_one()
    assert payment.amount_expected == 499
    assert payment.currency == "usd"
    assert payment.status == "pending"
    # Redirect alone never upgrades the plan.
    assert user.plan == "Free"


def test_webhook_rejects_missing_and_invalid_signature(client, stripe_env):
    payload = _completed_event("cs_test_1", 1)
    assert _post_webhook(client, payload, None).status_code == 400
    assert _post_webhook(client, payload, _sign(payload, secret="whsec_wrong")).status_code == 400
    stale = _sign(payload, timestamp=int(time.time()) - 3600)
    assert _post_webhook(client, payload, stale).status_code == 400
    assert db.session.execute(select(StripeEvent)).first() is None


def test_valid_webhook_upgrades_plan_and_duplicate_is_ignored(client, app, stripe_env):
    headers = _login(client)
    session_id = client.post(
        "/api/payments/checkout", json={"plan": "pro", "cycle": "monthly"}, headers=headers
    ).get_json()["session_id"]
    user_id = _user(app).id

    payload = _completed_event(session_id, user_id)
    first = _post_webhook(client, payload, _sign(payload))
    assert first.status_code == 200
    assert first.get_json()["outcome"] == "processed"

    db.session.expire_all()
    payment = db.session.execute(select(Payment)).scalar_one()
    assert payment.status == "paid"
    assert payment.amount_total == 499
    assert payment.stripe_subscription_id == "sub_123"
    assert _user(app).plan == "Pro"

    # Same event delivered again: acknowledged, not re-applied.
    _user(app).plan = "Free"
    db.session.commit()
    second = _post_webhook(client, payload, _sign(payload))
    assert second.status_code == 200
    assert second.get_json()["outcome"] == "duplicate"
    db.session.expire_all()
    assert _user(app).plan == "Free"
    assert len(db.session.execute(select(StripeEvent)).all()) == 1

    status = client.get(f"/api/payments/sessions/{session_id}")
    assert status.status_code == 200
    assert status.get_json()["status"] == "paid"


def test_webhook_with_mismatched_user_reference_does_not_upgrade(client, app, stripe_env):
    headers = _login(client)
    session_id = client.post(
        "/api/payments/checkout", json={"plan": "pro", "cycle": "monthly"}, headers=headers
    ).get_json()["session_id"]

    payload = _completed_event(session_id, user_id=999_999, event_id="evt_mismatch")
    assert _post_webhook(client, payload, _sign(payload)).status_code == 200
    db.session.expire_all()
    assert db.session.execute(select(Payment)).scalar_one().status == "pending"
    assert _user(app).plan == "Free"


def test_subscription_deleted_downgrades_to_free(client, app, stripe_env):
    headers = _login(client)
    session_id = client.post(
        "/api/payments/checkout", json={"plan": "pro", "cycle": "monthly"}, headers=headers
    ).get_json()["session_id"]
    completed = _completed_event(session_id, _user(app).id)
    _post_webhook(client, completed, _sign(completed))

    user_id = _user(app).id
    foreign = json.dumps({
        "id": "evt_deleted_foreign",
        "type": "customer.subscription.deleted",
        "data": {"object": {"id": "sub_123", "customer": "cus_123", "metadata": {"fence_user_id": "424242"}}},
    })
    response = _post_webhook(client, foreign, _sign(foreign))
    assert response.get_json()["outcome"] == "rejected"
    db.session.expire_all()
    assert _user(app).plan == "Pro"

    deleted = json.dumps({
        "id": "evt_deleted",
        "type": "customer.subscription.deleted",
        "data": {"object": {"id": "sub_123", "customer": "cus_123", "metadata": {"fence_user_id": str(user_id)}}},
    })
    assert _post_webhook(client, deleted, _sign(deleted)).status_code == 200
    db.session.expire_all()
    assert db.session.execute(select(Payment)).scalar_one().status == "canceled"
    assert _user(app).plan == "Free"


def test_checkout_sends_user_id_both_ways_and_plan_in_metadata(client, app, stripe_env):
    headers = _login(client)
    _start_checkout(client, headers)
    params = stripe_env[0]
    user_id = str(_user(app).id)
    assert params["client_reference_id"] == user_id
    assert params["metadata"] == {"fence_user_id": user_id, "plan": "pro", "cycle": "monthly"}
    # The subscription keeps the same ids so later subscription events can be verified too.
    assert params["subscription_data"]["metadata"] == params["metadata"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"client_reference_id": None},
        {"metadata": {}},
        {"metadata": {"fence_user_id": "999999", "plan": "pro", "cycle": "monthly"}},
        {"metadata": {"plan": "enterprise", "cycle": "monthly"}},
        {"metadata": {"plan": "pro", "cycle": "yearly"}},
    ],
    ids=["no-reference", "no-metadata", "foreign-metadata-user", "tampered-plan", "tampered-cycle"],
)
def test_webhook_rejects_any_identity_mismatch(client, app, stripe_env, overrides):
    headers = _login(client)
    session_id = _start_checkout(client, headers)
    user_id = _user(app).id
    if "metadata" in overrides and overrides["metadata"]:
        overrides["metadata"] = {"fence_user_id": str(user_id), **overrides["metadata"]}

    payload = _completed_event(session_id, user_id, event_id="evt_bad", **overrides)
    response = _post_webhook(client, payload, _sign(payload))
    assert response.status_code == 200
    assert response.get_json()["outcome"] == "rejected"
    db.session.expire_all()
    assert db.session.execute(select(Payment)).scalar_one().status == "pending"
    assert _user(app).plan == "Free"


def test_webhook_rejects_customer_switch_on_known_payment(client, app, stripe_env):
    headers = _login(client)
    session_id = _start_checkout(client, headers)
    payment = db.session.execute(select(Payment)).scalar_one()
    payment.stripe_customer_id = "cus_original"
    db.session.commit()

    payload = _completed_event(session_id, _user(app).id, customer="cus_other")
    assert _post_webhook(client, payload, _sign(payload)).get_json()["outcome"] == "rejected"
    db.session.expire_all()
    assert _user(app).plan == "Free"


def test_webhook_recovers_lost_payment_row_from_consistent_ids(client, app, stripe_env):
    _login(client)
    user_id = _user(app).id
    payload = _completed_event("cs_lost_row", user_id, event_id="evt_recover")
    response = _post_webhook(client, payload, _sign(payload))
    assert response.get_json()["outcome"] == "processed"
    db.session.expire_all()
    payment = db.session.execute(select(Payment)).scalar_one()
    assert payment.checkout_session_id == "cs_lost_row"
    assert payment.user_id == user_id
    assert payment.status == "paid"
    assert _user(app).plan == "Pro"


def test_webhook_does_not_recover_unknown_session_with_inconsistent_ids(client, app, stripe_env):
    _login(client)
    user_id = _user(app).id
    payload = _completed_event(
        "cs_lost_row",
        user_id,
        event_id="evt_recover_bad",
        metadata={"fence_user_id": str(user_id + 1), "plan": "pro", "cycle": "monthly"},
    )
    assert _post_webhook(client, payload, _sign(payload)).get_json()["outcome"] == "rejected"
    db.session.expire_all()
    assert db.session.execute(select(Payment)).first() is None
    assert _user(app).plan == "Free"


def test_payment_status_is_owner_only(client, stripe_env):
    _login(client)
    assert client.get("/api/payments/sessions/cs_unknown").status_code == 404
