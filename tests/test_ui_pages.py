"""Server-rendered quick UI: auth redirects and the scenario → projection pages render."""

from unittest.mock import MagicMock

from tests.test_simulations import _assumptions, _projection_payload


def _login(client, monkeypatch):
    store = {}
    fake_redis = MagicMock()
    fake_redis.setex.side_effect = lambda key, ttl, value: store.__setitem__(key, value)
    fake_redis.get.side_effect = store.get
    fake_redis.getdel.side_effect = lambda key: store.pop(key, None)
    fake_redis.delete.side_effect = lambda key: store.pop(key, None)
    monkeypatch.setattr("app.core.redis_client.get_redis", lambda: fake_redis)
    response = client.post("/api/auth/register", json={"email": "ui@example.com", "password": "Passw0rd!"})
    assert response.status_code == 201
    return {"X-CSRF-Token": client.get_cookie("csrf_token").value}


def test_ui_redirects_anonymous_users_to_login(client):
    response = client.get("/ui/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/login")
    assert client.get("/ui/login").status_code == 200


def test_ui_renders_scenario_with_projection(client, monkeypatch):
    headers = _login(client, monkeypatch)
    scenario = client.post(
        "/api/simulations", json={"name": "UI path", "assumptions": _assumptions()}, headers=headers
    ).get_json()
    projection = client.post(
        f"/api/simulations/{scenario['id']}/revisions/1/projections",
        json=_projection_payload(),
        headers=headers,
    )
    assert projection.status_code == 201

    listing = client.get("/ui/")
    assert listing.status_code == 200
    assert "UI path" in listing.get_data(as_text=True)

    detail = client.get(f"/ui/scenarios/{scenario['id']}")
    page = detail.get_data(as_text=True)
    assert detail.status_code == 200
    assert "94 000 PLN" in page  # total investment from the hand-checked reference case
    assert "59.6%" in page
    assert "data-ai-run" in page

    assert client.get("/ui/scenarios/999999").status_code == 404
    assert client.get("/ui/new").status_code == 200
