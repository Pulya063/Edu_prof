"""Redis client singleton for refresh token storage."""
import logging
import os

import redis

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _client = redis.Redis.from_url(url, decode_responses=True)
        logger.info("Redis client initialised url=%s", url)
    return _client


def init_redis(app=None) -> None:
    """Eagerly verify the Redis connection on app startup."""
    try:
        get_redis().ping()
        logger.info("Redis connection verified OK")
    except redis.exceptions.ConnectionError as exc:
        logger.warning("Redis not reachable at startup: %s", exc)


_REFRESH_PREFIX = "refresh:"


def store_refresh_token(token: str, user_id: int, ttl_seconds: int) -> None:
    """Store token -> user_id mapping in Redis with the given TTL."""
    get_redis().setex(f"{_REFRESH_PREFIX}{token}", ttl_seconds, str(user_id))
    logger.debug("Stored refresh token for user_id=%s ttl=%ss", user_id, ttl_seconds)


def get_user_id_by_refresh_token(token: str) -> int | None:
    """Return the user_id associated with token, or None if not found/expired."""
    value = get_redis().get(f"{_REFRESH_PREFIX}{token}")
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def delete_refresh_token(token: str) -> None:
    """Revoke token by removing it from Redis."""
    get_redis().delete(f"{_REFRESH_PREFIX}{token}")
    logger.debug("Revoked refresh token")
