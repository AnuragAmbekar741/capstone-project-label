# app/celery_app.py
from celery import Celery
from app.config import settings
import os

# Redis URL for Celery broker and result backend
REDIS_URL = os.environ.get("REDIS_URL")

# Create Celery app
celery_app = Celery(
    "capstone_project_label",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.token_refresh"]  # Include task modules
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Celery Beat schedule configuration
celery_app.conf.beat_schedule = {
    "refresh-gmail-tokens": {
        "task": "app.tasks.token_refresh.refresh_expiring_gmail_tokens",
        "schedule": 10.0,  # Run every 10 minutes
    },
}