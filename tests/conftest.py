import os

# Keep tests off the real Redis broker/result store; must be set before app imports
# (load_dotenv() does not override variables that are already set).
os.environ["CELERY_BROKER_URL"] = "memory://"
os.environ["CELERY_RESULT_BACKEND"] = "cache+memory://"
# The advisory AI reviewer stays off in tests unless a test enables it explicitly.
os.environ["DEEP_AGENT_MODEL"] = ""

import pytest
from flask import Flask

from app.main import create_app
from app.core.database import db
from app.core.rate_limit import reset_in_memory_rate_limits


@pytest.fixture(autouse=True)
def reset_rate_limits():
    reset_in_memory_rate_limits()
    yield
    reset_in_memory_rate_limits()

@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> Flask:
    """Створює екземпляр Flask для тестування з in-memory SQLite БД."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    app = create_app()
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key"
    })

    # Створюємо таблиці перед тестами
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Тестовий HTTP клієнт Flask."""
    return app.test_client()

@pytest.fixture
def db_session(app):
    """Фікстура сесії бази даних для доступу до БД напряму з тестів."""
    with app.app_context():
        yield db.session
