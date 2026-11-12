from app.scripts.generate_ts_types import OUTPUT_PATH, generate


def test_frontend_api_types_match_pydantic_schemas():
    committed = OUTPUT_PATH.read_text(encoding="utf-8")
    assert committed == generate(), (
        "frontend/lib/api/generated.ts is stale. Run: uv run --no-sync python -m app.scripts.generate_ts_types"
    )


def test_decimals_are_numbers_and_datetimes_are_strings():
    generated = generate()
    assert "DecimalString" not in generated
    assert "total_investment: number;" in generated
    assert "roi_percent: number | null;" in generated
    assert "baseline_annual_salary: number;" in generated
    assert "created_at: IsoDateTime;" in generated


def test_api_decimal_serializes_as_json_number():
    from decimal import Decimal

    from app.schemas import TuitionSnapshotResponse

    field = TuitionSnapshotResponse.model_fields["annual_tuition"]
    assert field.annotation is Decimal
    from pydantic import TypeAdapter

    from app.schemas import ApiDecimal

    adapter = TypeAdapter(ApiDecimal | None)
    assert adapter.dump_python(Decimal("60000.00"), mode="json") == 60000.0
    assert adapter.dump_python(Decimal("12.5")) == Decimal("12.5")
    assert adapter.dump_python(None, mode="json") is None


def _fake_redis():
    from unittest.mock import MagicMock

    store = {}
    client = MagicMock()
    client.setex.side_effect = lambda key, ttl, value: store.__setitem__(key, value)
    client.get.side_effect = store.get
    client.getdel.side_effect = lambda key: store.pop(key, None)
    client.delete.side_effect = lambda key: store.pop(key, None)
    return client


def test_workspace_state_and_me_keep_their_shape(client, monkeypatch):
    from sqlalchemy import select

    from app.core.database import db
    from app.models import User, UserRoadmap

    monkeypatch.setattr("app.core.redis_client.get_redis", lambda: _fake_redis())
    assert client.post("/api/auth/register", json={"email": "shape@example.com", "password": "Passw0rd!"}).status_code == 201

    state = client.get("/api/workspace")
    assert state.status_code == 200
    body = state.get_json()
    assert set(body["user"]) == {"id", "username", "email", "plan", "scenario_count", "scenario_limit"}
    assert body["roadmap"] is None

    user = db.session.execute(select(User).where(User.email == "shape@example.com")).scalar_one()
    db.session.add(UserRoadmap(user_id=user.id, target_job="Data Analyst", roadmap_data={}))
    db.session.commit()
    # Roadmap is admin-only: a regular user does not see it even when one is stored.
    assert client.get("/api/workspace").get_json()["roadmap"] is None
    user.is_admin = True
    db.session.commit()
    roadmap = client.get("/api/workspace").get_json()["roadmap"]
    assert roadmap["target_job"] == "Data Analyst"
    assert isinstance(roadmap["plan"], dict)
    assert "T" in roadmap["updated_at"]

    me = client.get("/api/auth/me").get_json()
    assert set(me) == {
        "id", "email", "username", "created_at", "plan", "plan_limits",
        "plan_features", "usage", "calculations_remaining", "is_admin",
    }
