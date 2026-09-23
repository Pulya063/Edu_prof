"""Tests for refresh token flow: login, refresh, revocation, logout.

All Redis interactions are mocked via unittest.mock to avoid a real Redis connection.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.main import create_app
from app.core.database import db


def _fake_redis_store():
    """In-memory dict that mimics the Redis refresh token store."""
    store: dict = {}

    def setex(key, ttl, value):
        store[key] = value

    def get(key):
        return store.get(key)

    def delete(key):
        store.pop(key, None)

    m = MagicMock()
    m.setex.side_effect = setex
    m.get.side_effect = get
    m.delete.side_effect = delete
    m.ping.return_value = True
    return m, store


@pytest.fixture()
def app_with_redis(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-long-enough")
    monkeypatch.setenv("ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")

    fake_redis, store = _fake_redis_store()

    with patch("app.core.redis_client.get_redis", return_value=fake_redis):
        app = create_app()
        app.config.update({"TESTING": True, "WTF_CSRF_ENABLED": False})
        with app.app_context():
            db.create_all()
            yield app, store
            db.session.remove()
            db.drop_all()


@pytest.fixture()
def client(app_with_redis):
    app, _ = app_with_redis
    return app.test_client()


@pytest.fixture()
def redis_store(app_with_redis):
    _, store = app_with_redis
    return store


_REG_PAYLOAD = {"email": "refresh@example.com", "password": "Passw0rd!"}


def test_login_sets_both_cookies(client):
    """POST /login should set both access_token and refresh_token cookies."""
    client.post("/api/auth/register", json=_REG_PAYLOAD)
    resp = client.post("/api/auth/login", json=_REG_PAYLOAD)
    assert resp.status_code == 200
    assert client.get_cookie("access_token") is not None
    assert client.get_cookie("refresh_token") is not None


def test_register_sets_both_cookies(client):
    """POST /register should set both access_token and refresh_token cookies."""
    resp = client.post("/api/auth/register", json=_REG_PAYLOAD)
    assert resp.status_code in (200, 201)
    assert client.get_cookie("access_token") is not None
    assert client.get_cookie("refresh_token") is not None


def test_refresh_returns_new_tokens(client):
    """POST /refresh should issue a new pair and revoke the old refresh token."""
    client.post("/api/auth/register", json=_REG_PAYLOAD)
    client.post("/api/auth/login", json=_REG_PAYLOAD)

    old_refresh = client.get_cookie("refresh_token").value
    assert old_refresh

    resp = client.post("/api/auth/refresh")
    assert resp.status_code == 200

    new_refresh = client.get_cookie("refresh_token").value
    assert new_refresh != old_refresh, "Refresh token should be rotated"


def test_refresh_twice_with_old_token_fails(client):
    """Using a rotated (old) refresh token should return 401."""
    client.post("/api/auth/register", json=_REG_PAYLOAD)
    client.post("/api/auth/login", json=_REG_PAYLOAD)

    old_refresh = client.get_cookie("refresh_token").value

    # First refresh succeeds, old token is now revoked in fake Redis
    resp = client.post("/api/auth/refresh")
    assert resp.status_code == 200

    # Re-inject the revoked old token to simulate theft / replay
    client.set_cookie("refresh_token", old_refresh)

    resp = client.post("/api/auth/refresh")
    assert resp.status_code == 401, "Re-using revoked refresh token must fail"


def test_logout_clears_cookies_and_revokes(client, redis_store):
    """POST /logout should revoke the refresh token from Redis."""
    client.post("/api/auth/register", json=_REG_PAYLOAD)
    client.post("/api/auth/login", json=_REG_PAYLOAD)

    refresh_token = client.get_cookie("refresh_token").value
    redis_key = f"refresh:{refresh_token}"
    assert redis_key in redis_store

    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    assert redis_key not in redis_store


def test_refresh_without_cookie_returns_401(client):
    """POST /refresh with no refresh_token cookie should return 401."""
    # Ensure no cookies are set
    resp = client.post("/api/auth/refresh")
    assert resp.status_code == 401


def test_me_after_silent_refresh(client):
    """When the access token is missing, the refresh token should silently renew it."""
    client.post("/api/auth/register", json=_REG_PAYLOAD)
    client.post("/api/auth/login", json=_REG_PAYLOAD)

    # Delete access_token to simulate expiry
    client.delete_cookie("access_token")
    assert client.get_cookie("access_token") is None
    assert client.get_cookie("refresh_token") is not None

    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "email" in data
    assert data["email"] == _REG_PAYLOAD["email"]