"""Redis-backed fixed-window limits for sensitive endpoints."""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import current_app, request
from redis.exceptions import RedisError

from app.core.exceptions import AppError
from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)
_memory_counts: dict[str, int] = {}
_memory_lock = threading.Lock()


def reset_in_memory_rate_limits() -> None:
    with _memory_lock:
        _memory_counts.clear()


def normalized_email_rate_key() -> str:
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    return hashlib.sha256(email.encode()).hexdigest() if email else "missing"


def _client_key() -> str:
    # Do not trust forwarded headers until Flask is configured with a known proxy chain.
    return request.remote_addr or "unknown"


def _increment(key: str, window_seconds: int) -> int:
    if current_app.testing:
        with _memory_lock:
            count = _memory_counts.get(key, 0) + 1
            _memory_counts[key] = count
            return count
    try:
        pipeline = get_redis().pipeline(transaction=True)
        pipeline.incr(key)
        pipeline.expire(key, window_seconds + 1)
        return int(pipeline.execute()[0])
    except RedisError as error:
        logger.warning("Rate-limit storage unavailable; allowing request: %s", error)
        return 0


def rate_limit(limit: int, window_seconds: int, scope: str, *, key_func: Callable[[], str] | None = None):
    def decorator(func: Callable[..., Any]):
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            if not current_app.config.get("RATE_LIMITING_ENABLED", True):
                return func(*args, **kwargs)
            identity = (key_func or _client_key)()
            bucket = int(time.time()) // window_seconds
            digest = hashlib.sha256(identity.encode()).hexdigest()
            count = _increment(f"rate_limit:{scope}:{digest}:{bucket}", window_seconds)
            if count > limit:
                retry_after = window_seconds - (int(time.time()) % window_seconds)
                raise AppError(
                    "Забагато запитів. Спробуйте пізніше.",
                    status_code=429,
                    headers={"Retry-After": str(retry_after)},
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator
