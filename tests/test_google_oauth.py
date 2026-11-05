from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from authlib.integrations.base_client.errors import OAuthError
from flask import redirect
from sqlalchemy import func, select

from app.core.database import db
from app.main import create_app
from app.models import User

FRONTEND = "http://localhost:3221"


def _fake_redis():
    store = {}
    client = MagicMock()
    client.ping.return_value = True
    client.setex.side_effect = lambda key, ttl, value: store.__setitem__(key, value)
    client.get.side_effect = store.get
    client.getdel.side_effect = lambda key: store.pop(key, None)
    client.delete.side_effect = lambda key: store.pop(key, None)
    return client


def _make_client(monkeypatch, configured: bool):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "oauth-test-secret")
    monkeypatch.setenv("FRONTEND_URL", FRONTEND)
    monkeypatch.delenv("OAUTH_REDIRECT_URI", raising=False)
    monkeypatch.delenv("OAUTH_SUCCESS_URL", raising=False)
    if configured:
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")
    else:
        monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    app = create_app()
    app.config.update(TESTING=True)
    return app


@pytest.fixture
def unconfigured(monkeypatch):
    with patch("app.core.redis_client.get_redis", return_value=_fake_redis()):
        app = _make_client(monkeypatch, configured=False)
        with app.app_context():
            db.create_all()
            yield app.test_client()
            db.session.remove()
            db.drop_all()


@pytest.fixture
def google(monkeypatch):
    """Configured app whose Google client is replaced by a fake (no network)."""
    fake = SimpleNamespace(redirect_uris=[], userinfo=None, error=None)

    def authorize_redirect(redirect_uri):
        fake.redirect_uris.append(redirect_uri)
        return redirect("https://accounts.google.com/o/oauth2/v2/auth?state=test")

    def authorize_access_token():
        if fake.error:
            raise fake.error
        return {"userinfo": fake.userinfo}

    with patch("app.core.redis_client.get_redis", return_value=_fake_redis()):
        app = _make_client(monkeypatch, configured=True)
        monkeypatch.setattr(
            "app.core.oauth.oauth",
            SimpleNamespace(google=SimpleNamespace(
                authorize_redirect=authorize_redirect,
                authorize_access_token=authorize_access_token,
            )),
        )
        with app.app_context():
            db.create_all()
            fake.client = app.test_client()
            yield fake
            db.session.remove()
            db.drop_all()


def test_providers_reports_unconfigured_and_login_is_503_not_500(unconfigured):
    assert unconfigured.get("/api/auth/providers").get_json() == {"google": {"configured": False}}
    assert unconfigured.get("/api/auth/login/google").status_code == 503
    assert unconfigured.get("/api/auth/callback/google?code=x&state=y").status_code == 503


def test_providers_reports_configured(google):
    assert google.client.get("/api/auth/providers").get_json() == {"google": {"configured": True}}


def test_login_redirects_with_frontend_callback_uri(google):
    response = google.client.get("/api/auth/login/google")
    assert response.status_code == 302
    assert response.headers["Location"].startswith("https://accounts.google.com/")
    assert google.redirect_uris == [f"{FRONTEND}/api/auth/callback/google"]


@pytest.mark.parametrize(
    ("next_path", "stored"),
    [
        ("/payment?plan=pro&cycle=monthly", "/payment?plan=pro&cycle=monthly"),
        ("/workspace/scenarios", "/workspace/scenarios"),
        ("https://evil.example/steal", None),
        ("//evil.example", None),
        ("/admin", None),
    ],
)
def test_login_only_keeps_safe_next_paths(google, next_path, stored):
    google.client.get("/api/auth/login/google", query_string={"next": next_path})
    with google.client.session_transaction() as session:
        assert session.get("oauth_next") == stored


def test_callback_cancel_redirects_to_login_with_reason(google):
    response = google.client.get("/api/auth/callback/google?error=access_denied")
    assert response.status_code == 302
    assert response.headers["Location"] == f"{FRONTEND}/login?oauth_error=cancelled"


def test_callback_token_exchange_failure_redirects_instead_of_500(google):
    google.error = OAuthError(error="mismatching_state")
    response = google.client.get("/api/auth/callback/google?code=x&state=y")
    assert response.status_code == 302
    assert response.headers["Location"] == f"{FRONTEND}/login?oauth_error=google_failed"
    assert google.client.get_cookie("access_token") is None


def test_unverified_google_email_never_signs_into_existing_account(google):
    google.client.post("/api/auth/register", json={"email": "owner@example.com", "password": "Passw0rd!"})
    google.client.delete_cookie("access_token")
    google.client.delete_cookie("refresh_token")
    google.userinfo = {"email": "owner@example.com", "email_verified": False}

    response = google.client.get("/api/auth/callback/google?code=x&state=y")
    assert response.headers["Location"] == f"{FRONTEND}/login?oauth_error=email_unverified"
    assert google.client.get_cookie("access_token") is None


def test_verified_new_user_is_created_and_lands_in_workspace(google):
    google.userinfo = {"email": "New.Person@Example.com", "email_verified": True}
    response = google.client.get("/api/auth/callback/google?code=x&state=y")
    assert response.status_code == 302
    assert response.headers["Location"] == f"{FRONTEND}/workspace/overview"
    assert google.client.get_cookie("access_token") is not None
    assert google.client.get_cookie("refresh_token") is not None
    assert google.client.get_cookie("csrf_token") is not None
    user = db.session.execute(select(User)).scalar_one()
    assert user.email == "new.person@example.com"

    me = google.client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.get_json()["email"] == "new.person@example.com"


def test_existing_user_matched_case_insensitively_and_next_is_honoured(google):
    google.client.post("/api/auth/register", json={"email": "owner@example.com", "password": "Passw0rd!"})
    google.client.get("/api/auth/login/google", query_string={"next": "/payment?plan=pro&cycle=yearly"})
    google.userinfo = {"email": "OWNER@example.com", "email_verified": True}

    response = google.client.get("/api/auth/callback/google?code=x&state=y")
    assert response.headers["Location"] == f"{FRONTEND}/payment?plan=pro&cycle=yearly"
    assert db.session.scalar(select(func.count(User.id))) == 1


def test_disabled_account_cannot_sign_in_with_google(google):
    google.client.post("/api/auth/register", json={"email": "off@example.com", "password": "Passw0rd!"})
    google.client.delete_cookie("access_token")
    google.client.delete_cookie("refresh_token")
    user = db.session.execute(select(User)).scalar_one()
    user.is_active = False
    db.session.commit()
    google.userinfo = {"email": "off@example.com", "email_verified": True}

    response = google.client.get("/api/auth/callback/google?code=x&state=y")
    assert response.headers["Location"] == f"{FRONTEND}/login?oauth_error=account_disabled"
    assert google.client.get_cookie("access_token") is None
