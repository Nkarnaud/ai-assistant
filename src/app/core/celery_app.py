"""Celery application for background task processing."""

from celery import Celery

from .config import settings

# Create Celery app
celery_app = Celery(
    "ai_assistant",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.core.celery_tasks"],
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
)

# Periodic tasks configuration
celery_app.conf.beat_schedule = {
    "check-upcoming-events": {
        "task": "app.core.celery_tasks.check_upcoming_events",
        "schedule": 60.0,  # Every minute
    },
    "renew-gmail-watch": {
        "task": "app.core.celery_tasks.renew_gmail_watch_subscriptions",
        "schedule": 86400.0,  # Every day
    },
}
