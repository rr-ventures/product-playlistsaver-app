import logging

from celery import Celery
from celery.signals import task_failure, task_retry, worker_init

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("playlist_saver.celery")

celery = Celery("playlist_saver", broker=settings.redis_url, backend=settings.redis_url)
celery.conf.timezone = "UTC"
celery.conf.beat_schedule = {
    "daily-playlist-check": {
        "task": "app.tasks.playlist_tasks.run_daily_checks",
        "schedule": 60 * 60 * 24,
    }
}


@worker_init.connect
def on_worker_init(**kwargs):
    from app.utils.logging import configure_logging
    configure_logging()
    logger.info("Celery worker initialized")


@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None, traceback=None, **kwargs):
    logger.error(
        "Celery task failed",
        extra={
            "task_name": sender.name if sender else "unknown",
            "task_id": task_id,
            "exception_type": type(exception).__name__ if exception else None,
            "exception_message": str(exception) if exception else None,
        },
    )


@task_retry.connect
def on_task_retry(sender=None, request=None, reason=None, **kwargs):
    logger.warning(
        "Celery task retrying",
        extra={
            "task_name": sender.name if sender else "unknown",
            "task_id": request.id if request else None,
            "reason": str(reason) if reason else None,
        },
    )
