from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.models import SubscriptionTier, User
from app.services.stripe_service import StripeService

router = APIRouter(prefix="/api/payments", tags=["payments"])
stripe_service = StripeService()


class CheckoutRequest(BaseModel):
    plan: str


@router.post("/checkout")
async def checkout(payload: CheckoutRequest, current_user: User = Depends(get_current_user)):
    stripe_service.require_enabled()
    return {"message": "Stripe checkout session would be created", "plan": payload.plan, "user": str(current_user.id)}


@router.post("/webhook")
async def webhook():
    stripe_service.require_enabled()
    return {"message": "Stripe webhook received"}


@router.get("/subscription")
async def subscription(current_user: User = Depends(get_current_user)):
    return {
        "tier": current_user.subscription_tier,
        "status": "inactive" if current_user.subscription_tier == SubscriptionTier.FREE else "active",
    }


@router.post("/cancel")
async def cancel(current_user: User = Depends(get_current_user)):
    stripe_service.require_enabled()
    return {"message": f"Subscription cancel requested for user {current_user.id}"}


@router.post("/portal")
async def portal(current_user: User = Depends(get_current_user)):
    stripe_service.require_enabled()
    return {"message": f"Customer portal requested for user {current_user.id}"}
