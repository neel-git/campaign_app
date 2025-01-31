from celery import Celery
from django.conf import settings
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Initialize Celery app
app = Celery("campaign_management")

# Load configuration from Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Configure Celery
app.conf.update(
    broker_url="redis://localhost:6379/0",
    result_backend="redis://localhost:6379/1",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_pool_restarts=True,
    broker_connection_retry_on_startup=True,
)

# Set up periodic tasks
app.conf.beat_schedule = {
    "check-scheduled-campaigns": {
        "task": "campaigns.tasks.check_scheduled_campaigns",
        "schedule": 60.0,  # Run every minute
    },
}

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()
