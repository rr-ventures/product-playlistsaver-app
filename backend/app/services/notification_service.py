import logging
from datetime import UTC, datetime

import resend
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import NotificationLog, User

settings = get_settings()
logger = logging.getLogger("playlist_saver.notifications")


class NotificationService:
    async def send_track_removed_email(self, db: AsyncSession, user: User, playlist_name: str, tracks: list[str]) -> bool:
        subject = f"Tracks removed from {playlist_name}"
        body = "Removed tracks:\n" + "\n".join(f"- {name}" for name in tracks)
        delivery_status = "skipped"
        provider_message_id: str | None = None

        if settings.resend_api_key and settings.email_provider == "resend":
            try:
                resend.api_key = settings.resend_api_key
                result = resend.Emails.send(
                    {
                        "from": settings.email_from,
                        "to": [user.email],
                        "subject": subject,
                        "text": body,
                    }
                )
                provider_message_id = result.get("id") if isinstance(result, dict) else None
                delivery_status = "sent"
                logger.info(
                    "Email sent successfully",
                    extra={
                        "user_id": str(user.id),
                        "recipient": user.email,
                        "subject": subject,
                        "provider": "resend",
                        "provider_message_id": provider_message_id,
                        "track_count": len(tracks),
                    },
                )
            except Exception:
                delivery_status = "failed"
                logger.exception(
                    "Email delivery failed",
                    extra={
                        "user_id": str(user.id),
                        "recipient": user.email,
                        "subject": subject,
                        "provider": "resend",
                        "track_count": len(tracks),
                    },
                )
        else:
            logger.info(
                "Email skipped — provider not configured",
                extra={"user_id": str(user.id), "recipient": user.email},
            )

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
