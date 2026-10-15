import logging

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def refresh_market_snapshot(self, role: str, country: str, currency: str) -> dict:
    """Fetch and store salary data for a role/country pair from O*NET."""
    from app.core.database import db
    from app.main import app as flask_app
    from app.services.market_ingestion_service import MarketIngestionService

    try:
        with flask_app.app_context():
            result = MarketIngestionService(db.session).fetch_from_onet(role, country, currency)
            if result:
                snapshot, created = result
                return {
                    "role": role,
                    "snapshot_id": snapshot.id,
                    "created": created
                }
            return {"role": role, "snapshot_id": None, "created": False, "reason": "stub or not found"}
    except Exception as error:
        logger.warning("Market snapshot refresh failed for %s: %s", role, error)
        raise self.retry(exc=error)

@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def refresh_market_snapshot_batch(self, roles: list[dict] | None = None) -> dict:
    """Batch refresh market snapshots. roles = [{"role": "SE", "country": "US", "currency": "USD"}]"""
    if not roles:
        # Example default list for scheduled runs
        roles = [
            {"role": "Software Engineer", "country": "United States", "currency": "USD"},
            {"role": "Data Scientist", "country": "United States", "currency": "USD"}
        ]
        
    results = {"total": len(roles), "attempted": 0}
    for item in roles:
        refresh_market_snapshot.delay(item["role"], item.get("country", "United States"), item.get("currency", "USD"))
        results["attempted"] += 1
        
    return results
