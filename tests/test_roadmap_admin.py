from unittest.mock import MagicMock

from sqlalchemy import select

from app.core.database import db
from app.models import User, UserRoadmap


def _fake_redis():
    store = {}
    client = MagicMock()
    client.setex.side_effect = lambda key, ttl, value: store.__setitem__(key, value)
    client.get.side_effect = store.get
    client.getdel.side_effect = lambda key: store.pop(key, None)
    client.delete.side_effect = lambda key: store.pop(key, None)
    return client


def _register(client, monkeypatch, email):
    monkeypatch.setattr("app.core.redis_client.get_redis", lambda: _fake_redis())
    assert client.post("/api/auth/register", json={"email": email, "password": "Passw0rd!"}).status_code == 201
    return {"X-CSRF-Token": client.get_cookie("csrf_token").value}


def _roadmap_requests(client, headers, roadmap_id):
    json_accept = {**headers, "Accept": "application/json"}
    return {
        "get": client.get("/api/roadmap/", headers=json_accept),
        "generate": client.post("/api/roadmap/generate", json={"target_job": "Data Analyst", "hours_per_week": 10}, headers=headers),
        "preview": client.post("/api/workspace/roadmap/preview", json={"target_job": "Data Analyst", "current_level": "Beginner", "hours_per_week": 10}, headers=headers),
        "task": client.patch(f"/api/workspace/roadmaps/{roadmap_id}/tasks/t1", json={"completed": True}, headers=headers),
    }


def test_roadmap_endpoints_are_admin_only(client, monkeypatch):
    headers = _register(client, monkeypatch, "regular@example.com")
    user = db.session.execute(select(User).where(User.email == "regular@example.com")).scalar_one()
    roadmap = UserRoadmap(user_id=user.id, target_job="Data Analyst", roadmap_data={})
    db.session.add(roadmap)
    db.session.commit()

    for name, response in _roadmap_requests(client, headers, roadmap.id).items():
        assert response.status_code == 403, name
    assert client.get("/api/auth/me").get_json()["is_admin"] is False


def test_admin_can_use_roadmap(client, monkeypatch):
    headers = _register(client, monkeypatch, "boss@example.com")
    user = db.session.execute(select(User).where(User.email == "boss@example.com")).scalar_one()
    user.is_admin = True
    db.session.commit()

    assert client.get("/api/auth/me").get_json()["is_admin"] is True
    listed = client.get("/api/roadmap/", headers={"Accept": "application/json"})
    assert listed.status_code == 200
    assert listed.get_json()["data"] is None
    preview = client.post("/api/workspace/roadmap/preview", json={"target_job": "Data Analyst", "current_level": "Beginner", "hours_per_week": 10}, headers=headers)
    assert preview.status_code == 200
