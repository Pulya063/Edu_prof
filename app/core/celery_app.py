import os
from celery import Celery

def make_celery(app_name=__name__):
    broker_url = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
    backend_url = os.getenv("CELERY_RESULT_BACKEND", "rpc://")
    
    celery = Celery(
        app_name,
        broker=broker_url,
        backend=backend_url,
        include=['app.tasks.email_tasks']
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
