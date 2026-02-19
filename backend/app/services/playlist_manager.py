from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Playlist, PlaylistPlatform, Track, TrackRemovalEvent, User
from app.services.notification_service import NotificationService
from app.services.spotify_service import SpotifyService
from app.services.youtube_service import YouTubeService
from app.utils.encryption import decrypt_value


class PlaylistManager:
    def __init__(self) -> None:
        self.spotify = SpotifyService()
        self.youtube = YouTubeService()
        self.notification = NotificationService()

    async def _fetch_current_tracks(self, playlist: Playlist, user: User) -> list[dict]:
        if playlist.platform == PlaylistPlatform.SPOTIFY:
            token = decrypt_value(user.spotify_access_token)
            if not token:
                return []
            return await self.spotify.get_playlist_tracks(playlist.platform_playlist_id, token)
        token = decrypt_value(user.google_access_token)
        if not token:
            return []
        return await self.youtube.get_playlist_tracks(playlist.platform_playlist_id, token)

    async def check_playlist(self, db: AsyncSession, playlist: Playlist, user: User) -> dict[str, int]:
        now = datetime.now(UTC)
        current_tracks = await self._fetch_current_tracks(playlist, user)
        current_by_platform_id = {track["platform_track_id"]: track for track in current_tracks}

        existing_tracks = (
            await db.execute(select(Track).where(Track.playlist_id == playlist.id))
        ).scalars().all()
        existing_by_platform_id = {track.platform_track_id: track for track in existing_tracks}

        removed_names: list[str] = []

        for platform_track_id, existing in existing_by_platform_id.items():
            if platform_track_id not in current_by_platform_id and not existing.is_removed:
                existing.is_removed = True
                existing.removed_at = now
                removed_names.append(f"{existing.track_name} - {existing.artist_name}")
                db.add(
                    TrackRemovalEvent(
                        playlist_id=playlist.id,
                        track_id=existing.id,
                        detected_at=now,
                        notification_sent=False,
                    )
                )

        for idx, incoming in enumerate(current_tracks):
            platform_track_id = incoming["platform_track_id"]
            existing = existing_by_platform_id.get(platform_track_id)
            if existing:
                existing.track_name = incoming["track_name"]
                existing.artist_name = incoming["artist_name"]
                existing.position = idx
                existing.is_removed = False
                existing.last_seen_at = now
            else:
                db.add(
                    Track(
                        playlist_id=playlist.id,
                        platform_track_id=platform_track_id,
                        track_name=incoming["track_name"],
                        artist_name=incoming["artist_name"],
                        position=idx,
                        is_removed=False,
                        first_seen_at=now,
                        last_seen_at=now,
                    )
                )

        playlist.last_checked_at = now
        await db.commit()

        if removed_names:
            await self.notification.send_track_removed_email(db=db, user=user, playlist_name=playlist.name, tracks=removed_names)
            events = (
                await db.execute(
                    select(TrackRemovalEvent).where(
                        TrackRemovalEvent.playlist_id == playlist.id, TrackRemovalEvent.notification_sent.is_(False)
                    )
                )
            ).scalars().all()
            for event in events:
                event.notification_sent = True
                event.notification_sent_at = now
            await db.commit()

        return {"removed_count": len(removed_names), "current_count": len(current_tracks)}
