from celery import Celery

from app.config import get_settings

settings = get_settings()

celery = Celery("playlist_saver", broker=settings.redis_url, backend=settings.redis_url)
celery.conf.timezone = "UTC"
celery.conf.beat_schedule = {
    "daily-playlist-check": {
        "task": "app.tasks.playlist_tasks.run_daily_checks",
        "schedule": 60 * 60 * 24,
    }
}
