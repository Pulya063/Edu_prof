import logging

from app.core.celery_app import celery_app
from app.services.tuition_ingestion_service import (
    TuitionIngestionService,
    TuitionProviderConfigurationError,
    TuitionProviderError,
)


logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def refresh_college_scorecard_tuition(self, scorecard_id: int) -> dict[str, object]:
    """Fetch and normalize one College Scorecard institution outside request time."""
    from app.core.database import db
    from app.main import app as flask_app

    try:
        with flask_app.app_context():
            results = TuitionIngestionService(db.session).refresh_college_scorecard(scorecard_id)
            snapshot_ids = [snapshot.id for snapshot, _created in results]
            created_count = sum(1 for _snapshot, created in results if created)
        return {
            "provider": "college_scorecard",
            "scorecard_id": scorecard_id,
            "snapshot_ids": snapshot_ids,
            "created_count": created_count,
        }
    except TuitionProviderConfigurationError:
        logger.exception("College Scorecard tuition refresh is not configured")
        raise
    except TuitionProviderError as error:
        logger.warning("College Scorecard tuition refresh failed: %s", error)
        raise self.retry(exc=error)

@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def refresh_tuition_batch(self, scorecard_ids: list[int] | None = None) -> dict:
    """Refresh tuition snapshots for all watched US universities.
    Can be called manually with a list or scheduled (uses WATCHED_SCORECARD_IDS).
    """
    from app.core.watched_universities import get_watched_scorecard_ids
    ids_to_refresh = scorecard_ids if scorecard_ids else get_watched_scorecard_ids()
    results = {"total": len(ids_to_refresh), "created": 0, "skipped": 0, "failed": 0, "errors": []}
    
    for scorecard_id in ids_to_refresh:
        try:
            # We call the other task synchronously for the batch report
            # In a truly massive system, we'd spawn chords/groups. 
            # But here, we can just apply them or delay them.
            task_result = refresh_college_scorecard_tuition.apply(args=[scorecard_id])
            if task_result.failed():
                results["failed"] += 1
                results["errors"].append({"scorecard_id": scorecard_id, "error": str(task_result.result)})
            else:
                created_count = task_result.result.get("created_count", 0) if task_result.result else 0
                results["created"] += created_count
                results["skipped"] += 1 - min(created_count, 1)
        except Exception as exc:
            logger.warning("Batch tuition refresh failed for scorecard_id=%s: %s", scorecard_id, exc)
            results["failed"] += 1
            results["errors"].append({"scorecard_id": scorecard_id, "error": str(exc)})
            
    return results
