import asyncio

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models import Playlist, User
from app.services.playlist_manager import PlaylistManager
from app.tasks.celery_app import celery


@celery.task(name="app.tasks.playlist_tasks.run_daily_checks")
def run_daily_checks() -> int:
    return asyncio.run(_run_daily_checks())


async def _run_daily_checks() -> int:
    manager = PlaylistManager()
    processed = 0
    async with SessionLocal() as db:
        playlists = (await db.execute(select(Playlist).where(Playlist.is_active.is_(True)))).scalars().all()
        for playlist in playlists:
            user = await db.scalar(select(User).where(User.id == playlist.user_id))
            if not user:
                continue
            await manager.check_playlist(db, playlist, user)
            processed += 1
    return processed
