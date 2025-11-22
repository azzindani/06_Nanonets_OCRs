"""
Celery application for background task processing.
"""
import os
from celery import Celery

# Broker URL (Redis or RabbitMQ)
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# Create Celery app
celery_app = Celery(
    "nanonets",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["services.tasks"]
)

# Configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=600,  # 10 minutes max
    task_soft_time_limit=540,  # 9 minutes soft limit

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,

    # Result settings
    result_expires=3600,  # 1 hour

    # Queue configuration
    task_default_queue="default",
    task_queues={
        "default": {"exchange": "default", "routing_key": "default"},
        "high_priority": {"exchange": "high_priority", "routing_key": "high_priority"},
        "low_priority": {"exchange": "low_priority", "routing_key": "low_priority"},
        "gpu": {"exchange": "gpu", "routing_key": "gpu"},
    },

    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Beat schedule (periodic tasks)
    beat_schedule={
        "cleanup-expired-jobs": {
            "task": "services.tasks.cleanup_expired_jobs",
            "schedule": 3600.0,  # Every hour
        },
        "update-usage-metrics": {
            "task": "services.tasks.update_usage_metrics",
            "schedule": 300.0,  # Every 5 minutes
        },
    },
)


if __name__ == "__main__":
    celery_app.start()
