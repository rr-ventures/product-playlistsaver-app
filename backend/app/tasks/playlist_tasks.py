import asyncio
import logging
import time

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models import Playlist, User
from app.services.playlist_manager import PlaylistManager
from app.tasks.celery_app import celery

logger = logging.getLogger("playlist_saver.tasks")


@celery.task(
    name="app.tasks.playlist_tasks.run_daily_checks",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def run_daily_checks(self) -> dict:
    task_id = self.request.id
    logger.info("Daily playlist check started", extra={"task_id": task_id})
    start = time.monotonic()
    try:
        result = asyncio.run(_run_daily_checks(task_id))
        elapsed = round(time.monotonic() - start, 2)
        logger.info(
            "Daily playlist check completed",
            extra={"task_id": task_id, "elapsed_seconds": elapsed, **result},
        )
        return result
    except Exception:
        elapsed = round(time.monotonic() - start, 2)
        logger.exception(
            "Daily playlist check FAILED",
            extra={"task_id": task_id, "elapsed_seconds": elapsed},
        )
        raise


async def _run_daily_checks(task_id: str | None) -> dict:
    manager = PlaylistManager()
    processed = 0
    failed = 0
    total_removed = 0
    async with SessionLocal() as db:
        playlists = (await db.execute(select(Playlist).where(Playlist.is_active.is_(True)))).scalars().all()
        logger.info(
            "Found active playlists to check",
            extra={"task_id": task_id, "playlist_count": len(playlists)},
        )
        for playlist in playlists:
            user = await db.scalar(select(User).where(User.id == playlist.user_id))
            if not user:
                logger.warning(
                    "Skipping playlist — owner not found",
                    extra={"task_id": task_id, "playlist_id": str(playlist.id), "user_id": str(playlist.user_id)},
                )
                continue
            try:
                result = await manager.check_playlist(db, playlist, user)
                processed += 1
                total_removed += result.get("removed_count", 0)
                if result.get("removed_count", 0) > 0:
                    logger.info(
                        "Tracks removed detected",
                        extra={
                            "task_id": task_id,
                            "playlist_id": str(playlist.id),
                            "playlist_name": playlist.name,
                            "removed_count": result["removed_count"],
                        },
                    )
            except Exception:
                failed += 1
                logger.exception(
                    "Failed to check playlist",
                    extra={
                        "task_id": task_id,
                        "playlist_id": str(playlist.id),
                        "playlist_name": playlist.name,
                        "platform": playlist.platform.value,
                        "user_id": str(playlist.user_id),
                    },
                )
    return {"processed": processed, "failed": failed, "total_removed": total_removed}
