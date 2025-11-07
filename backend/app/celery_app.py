"""
Celery application configuration for background task processing
"""
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "fund_analysis_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.document_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Optional: Task routes
celery_app.conf.task_routes = {
    "app.tasks.document_tasks.process_document_task": {
        "queue": "document_processing"
    },
}

if __name__ == "__main__":
    celery_app.start()
