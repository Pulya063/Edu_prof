import logging

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=0, soft_time_limit=240, time_limit=300)
def review_projection_ai(self, projection_id: int) -> dict:
    """Run the advisory Deep Agent review for one stored projection."""
    from app.core.database import db
    from app.main import app as flask_app
    from app.models import SimulationProjection
    from app.services.projection_ai_review_service import ProjectionAIReviewService

    with flask_app.app_context():
        projection = db.session.get(SimulationProjection, projection_id)
        if projection is None:
            logger.warning("AI review skipped: projection_id=%s not found", projection_id)
            return {"projection_id": projection_id, "status": "missing"}
        review = ProjectionAIReviewService(db.session).review_best_effort(
            projection, projection.revision.assumptions
        )
        return {"projection_id": projection_id, "status": review.status}
