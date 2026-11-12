import json
import os
import logging
from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)

# Default list of well-known US universities (College Scorecard UNITID)
DEFAULT_WATCHED_SCORECARD_IDS: list[int] = [
    166683,  # MIT
    166027,  # Harvard University
    243744,  # Stanford University
    110635,  # UC Berkeley
    193900,  # New York University
    215062,  # University of Pennsylvania
    130794,  # Georgetown University
    186131,  # Princeton University
    130697,  # George Washington University
    199120,  # Duke University
]

WATCHED_REDIS_KEY = "tuition_watched_scorecard_ids"


def get_watched_scorecard_ids() -> list[int]:
    """Return the list of College Scorecard IDs to refresh automatically.
    Includes default, JSON env, and Redis-persisted IDs.
    """
    watched_set = set(DEFAULT_WATCHED_SCORECARD_IDS)
    
    env_value = os.getenv("WATCHED_SCORECARD_IDS")
    if env_value:
        try:
            ids = json.loads(env_value)
            if isinstance(ids, list):
                watched_set.update(i for i in ids if isinstance(i, int))
        except (json.JSONDecodeError, TypeError):
            pass
            
    try:
        redis_ids = get_redis().smembers(WATCHED_REDIS_KEY)
        watched_set.update(int(x) for x in redis_ids)
    except Exception as e:
        logger.warning("Could not read watched IDs from Redis: %s", e)
        
    return list(watched_set)


def add_watched_scorecard_id(scorecard_id: int) -> None:
    """Add a new scorecard_id to the watched list in Redis."""
    try:
        get_redis().sadd(WATCHED_REDIS_KEY, scorecard_id)
        logger.info("Added scorecard_id %s to auto-refresh list", scorecard_id)
    except Exception as e:
        logger.warning("Could not add scorecard_id %s to Redis: %s", scorecard_id, e)
