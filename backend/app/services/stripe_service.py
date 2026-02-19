from fastapi import HTTPException, status

from app.config import get_settings


class StripeService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def require_enabled(self) -> None:
        if not self.settings.payments_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payments are disabled in this build. Configure Stripe keys and PAYMENTS_ENABLED=true to enable.",
            )
