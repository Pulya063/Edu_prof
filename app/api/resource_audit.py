"""Small, read-only resource audit dashboard for local diagnostics."""

from __future__ import annotations

import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from flask import Blueprint, current_app, jsonify, render_template
import redis
from sqlalchemy import text

from app.core.database import db

blueprint = Blueprint("resource_audit", __name__)
ROOT = Path(__file__).resolve().parents[2]
BODY_EXAMPLES = {
    "/api/auth/register": {"email": "demo@example.com", "password": "DemoPass123", "confirm_password": "DemoPass123"},
    "/api/auth/login": {"email": "demo@example.com", "password": "DemoPass123"},
    "/api/auth/password-reset-request": {"email": "demo@example.com"},
    "/api/auth/password-reset": {"code": "000000", "new_password": "DemoPass123"},
    "/api/roi/calculate": {"university": "Demo University", "faculty": "Computer Science", "annual_tuition": 5000, "study_years": 4},
    "/api/roi/trial": {"university": "Demo University", "faculty": "Computer Science", "annual_tuition": 5000, "study_years": 4},
    "/api/roi/analyze": {"university": "Demo University", "degree": "Computer Science — Bachelor", "specialization_focus": "Web Development + Mobile Applications", "country": "United States", "currency": "USD", "study_years": 3.5, "monthly_payment": 930, "payments_per_year": 10, "additional_learning_budget_min": 0, "additional_learning_budget_max": 5000},
    "/api/mail/send": {"recipient": "demo@example.com", "subject": "Demo message", "body": "Test message from API Explorer"},
    "/roadmap/generate": {"target_job": "Python Developer", "hours_per_week": 10, "current_income": 0, "skills": ["Python", "SQL"]},
}


def _result(name: str, kind: str, status: str, detail: str, **extra: Any) -> dict[str, Any]:
    return {"name": name, "kind": kind, "status": status, "detail": detail, **extra}


def _timed(check: Any) -> tuple[str, str, float]:
    started = perf_counter()
    try:
        return "ok", str(check()), round((perf_counter() - started) * 1000, 1)
    except Exception as error:  # Diagnostics should report failures, not crash.
        return "error", str(error), round((perf_counter() - started) * 1000, 1)


def collect_resources() -> dict[str, Any]:
    resources: list[dict[str, Any]] = []

    status, detail, latency = _timed(lambda: db.session.execute(text("SELECT 1")).scalar() == 1)
    resources.append(_result("PostgreSQL / SQLAlchemy", "database", status, "Підключення працює" if status == "ok" else detail, latency_ms=latency))

    def redis_check() -> str:
        client = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
            socket_connect_timeout=0.4,
            socket_timeout=0.4,
        )
        return "PONG" if client.ping() else "Redis не відповів"

    status, detail, latency = _timed(redis_check)
    resources.append(_result("Redis", "service", status, detail if status == "ok" else "Недоступний: " + detail, latency_ms=latency))

    chroma_path = ROOT / "chroma_db" / "chroma.sqlite3"
    if chroma_path.exists():
        def chroma_check() -> str:
            with sqlite3.connect(chroma_path) as connection:
                connection.execute("SELECT 1").fetchone()
            return "SQLite OK"

        status, detail, latency = _timed(chroma_check)
        resources.append(_result("ChromaDB", "storage", status, f"SQLite-файл · {chroma_path.stat().st_size / 1024:.1f} KB" if status == "ok" else detail, latency_ms=latency))
    else:
        resources.append(_result("ChromaDB", "storage", "warning", "Файл chroma_db/chroma.sqlite3 не знайдено"))

    for relative, label, kind in [
        ("app/static/css/styles.css", "CSS assets", "asset"),
        ("app/static/js/app.js", "JavaScript assets", "asset"),
        ("frontend/package.json", "Next.js frontend", "frontend"),
        ("instance/dev_workspace.db", "Local workspace DB", "storage"),
    ]:
        path = ROOT / relative
        resources.append(_result(label, kind, "ok" if path.exists() else "error", f"{relative} · {path.stat().st_size / 1024:.1f} KB" if path.exists() else f"Не знайдено: {relative}"))

    for key in ["DATABASE_URL", "SECRET_KEY", "REDIS_URL", "DREAMWORK_API_URL", "COLLEGE_SCORECARD_API_KEY"]:
        configured = bool(os.getenv(key))
        resources.append(_result(key, "config", "ok" if configured else "warning", "Налаштовано" if configured else "Відсутнє (перевірте .env)"))

    routes = sorted({rule.rule for rule in current_app.url_map.iter_rules() if rule.rule != "/static/<path:filename>"})
    resources.extend(_result(route, "route", "ok", "Зареєстрований маршрут") for route in routes)

    counts = {"total": len(resources), "ok": sum(r["status"] == "ok" for r in resources), "warning": sum(r["status"] == "warning" for r in resources), "error": sum(r["status"] == "error" for r in resources)}
    endpoints = []
    for rule in sorted(current_app.url_map.iter_rules(), key=lambda item: (item.rule, sorted(item.methods))):
        if rule.rule.startswith("/static/") or rule.rule in {"/resources", "/api/resources"}:
            continue
        for method in sorted(rule.methods - {"HEAD", "OPTIONS"}):
            sample_path = rule.rule
            for variable in rule.arguments:
                sample_path = sample_path.replace(f"<int:{variable}>", "1").replace(f"<{variable}>", "example")
            endpoints.append({"method": method, "path": rule.rule, "sample_path": sample_path, "endpoint": rule.endpoint, "needs_body": method in {"POST", "PUT", "PATCH"}, "body_example": BODY_EXAMPLES.get(rule.rule, {}), "destructive": method == "DELETE"})

    return {"checked_at": datetime.now(UTC).isoformat(), "counts": counts, "resources": resources, "endpoints": endpoints}


@blueprint.get("/resources")
def resources_page() -> str:
    return render_template("resource_audit.html")


@blueprint.get("/api/resources")
def resources_api() -> Any:
    return jsonify(collect_resources())
