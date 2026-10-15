import os
from celery import Celery
from dotenv import load_dotenv

# Load .env before reading broker URL so this module is safe to import
# before main.py has had a chance to call load_dotenv().
load_dotenv()


def make_celery(app_name=__name__):
    broker_url = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
    backend_url = os.getenv("CELERY_RESULT_BACKEND", "rpc://")

    celery = Celery(
        app_name,
        broker=broker_url,
        backend=backend_url,
        include=[
            'app.tasks.email_tasks',
            'app.tasks.tuition_tasks',
            'app.tasks.market_tasks',
            'app.tasks.ai_review_tasks',
        ]
    )
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
    )
    return celery


celery_app = make_celery()

from celery.schedules import crontab  # noqa: E402

celery_app.conf.beat_schedule = {
    "refresh-us-tuition-weekly": {
        "task": "app.tasks.tuition_tasks.refresh_tuition_batch",
        "schedule": crontab(hour=2, minute=0, day_of_week=1),
        "args": ([],),  # empty list = use WATCHED_SCORECARD_IDS from config
    },
}
celery_app.conf.beat_dburi = os.getenv("DATABASE_URL")  # or default file-based
