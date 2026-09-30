from unittest.mock import MagicMock, patch

import pytest

from app.core.database import db
from app.main import create_app


def _fake_redis():
    store = {}
    client = MagicMock()
    client.ping.return_value = True
    client.setex.side_effect = lambda key, ttl, value: store.__setitem__(key, value)
    client.get.side_effect = store.get
    client.getdel.side_effect = lambda key: store.pop(key, None)
    client.delete.side_effect = lambda key: store.pop(key, None)
    return client


@pytest.fixture
def secure_client(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "phase0-test-secret")
    monkeypatch.setenv("ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    with patch("app.core.redis_client.get_redis", return_value=_fake_redis()):
        app = create_app()
        app.config.update(TESTING=True)
        with app.app_context():
            db.create_all()
            yield app.test_client()
            db.session.remove()
            db.drop_all()


def test_cookie_mutation_requires_csrf(secure_client):
    payload = {"email": "csrf@example.com", "password": "Passw0rd!"}
    assert secure_client.post("/api/auth/register", json=payload).status_code == 201
    assert secure_client.post("/api/auth/logout").status_code == 403
    token = secure_client.get_cookie("csrf_token").value
    assert secure_client.post("/api/auth/logout", headers={"X-CSRF-Token": token}).status_code == 200


def test_login_rate_limit(secure_client):
    payload = {"email": "missing@example.com", "password": "Passw0rd!"}
    for _ in range(10):
        assert secure_client.post("/api/auth/login", json=payload).status_code == 401
    assert secure_client.post("/api/auth/login", json=payload).status_code == 429


def test_google_oauth_unconfigured_returns_503(secure_client):
    assert secure_client.get("/api/auth/login/google").status_code == 503


def test_resource_audit_is_opt_in(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.delenv("ENABLE_RESOURCE_AUDIT", raising=False)
    app = create_app()
    assert "/api/resources" not in {rule.rule for rule in app.url_map.iter_rules()}

    monkeypatch.setenv("ENABLE_RESOURCE_AUDIT", "true")
    dev_app = create_app()
    assert "/api/resources" in {rule.rule for rule in dev_app.url_map.iter_rules()}

    monkeypatch.setenv("APP_ENV", "production")
    prod_app = create_app()
    assert "/api/resources" not in {rule.rule for rule in prod_app.url_map.iter_rules()}
