from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "task_manager",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# важно: чтобы воркер подхватил tasks
celery_app.autodiscover_tasks(["app.workers"])

celery_app.conf.task_track_started = True
