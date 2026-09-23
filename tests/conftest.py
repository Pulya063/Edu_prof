import pytest
from flask import Flask
from sqlalchemy.orm import Session

from app.main import create_app
from app.core.database import db

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
