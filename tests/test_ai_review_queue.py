"""The advisory AI review is queued to Celery instead of blocking the HTTP request."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.projection_ai_review_service import ProjectionAIReviewService


def _projection():
    return SimpleNamespace(id=42, ai_review=None)


def test_enqueue_without_model_is_not_configured(monkeypatch):
    monkeypatch.setenv("DEEP_AGENT_MODEL", "")
    delay = MagicMock()
    monkeypatch.setattr("app.tasks.ai_review_tasks.review_projection_ai.delay", delay)

    review = ProjectionAIReviewService(MagicMock()).enqueue(_projection())

    assert review.status == "not_configured"
    delay.assert_not_called()


def test_enqueue_openai_without_key_is_not_configured(monkeypatch):
    monkeypatch.setenv("DEEP_AGENT_MODEL", "openai:gpt-5-mini")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    review = ProjectionAIReviewService(MagicMock()).enqueue(_projection())

    assert review.status == "not_configured"
    assert review.error_message == "OPENAI_API_KEY is not configured"


def test_enqueue_queues_celery_task(monkeypatch):
    monkeypatch.setenv("DEEP_AGENT_MODEL", "openai:gpt-5-mini")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    delay = MagicMock()
    monkeypatch.setattr("app.tasks.ai_review_tasks.review_projection_ai.delay", delay)

    review = ProjectionAIReviewService(MagicMock()).enqueue(_projection())

    assert review.status == "pending"
    assert review.provider_model == "openai:gpt-5-mini"
    delay.assert_called_once_with(42)


def test_enqueue_marks_failed_when_queue_is_down(monkeypatch):
    monkeypatch.setenv("DEEP_AGENT_MODEL", "openai:gpt-5-mini")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.tasks.ai_review_tasks.review_projection_ai.delay",
        MagicMock(side_effect=ConnectionError("broker down")),
    )

    review = ProjectionAIReviewService(MagicMock()).enqueue(_projection())

    assert review.status == "failed"
    assert "broker down" in review.error_message
