from datetime import UTC, datetime

import resend
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import NotificationLog, User

settings = get_settings()


class NotificationService:
    async def send_track_removed_email(self, db: AsyncSession, user: User, playlist_name: str, tracks: list[str]) -> bool:
        subject = f"Tracks removed from {playlist_name}"
        body = "Removed tracks:\n" + "\n".join(f"- {name}" for name in tracks)
        delivery_status = "skipped"

        if settings.resend_api_key and settings.email_provider == "resend":
            resend.api_key = settings.resend_api_key
            resend.Emails.send(
                {
                    "from": settings.email_from,
                    "to": [user.email],
                    "subject": subject,
                    "text": body,
                }
            )
            delivery_status = "sent"

        db.add(
            NotificationLog(
                user_id=user.id,
                event_type="track_removed",
                subject=subject,
                body=body,
                delivery_status=delivery_status,
                sent_at=datetime.now(UTC),
            )
        )
        await db.commit()
        return delivery_status == "sent"
