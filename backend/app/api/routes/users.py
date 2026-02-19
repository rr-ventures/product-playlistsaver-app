from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models import NotificationLog, User
from app.schemas.common import UserOut, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> UserOut:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(current_user, key, value)
    await db.commit()
    await db.refresh(current_user)
    return UserOut.model_validate(current_user)


@router.delete("/me")
async def delete_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await db.delete(current_user)
    await db.commit()
    return {"message": "Account deleted"}


@router.get("/me/notifications")
async def notifications(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(select(NotificationLog).where(NotificationLog.user_id == current_user.id).limit(100))
    ).scalars().all()
    return [
        {
            "id": str(row.id),
            "event_type": row.event_type,
            "subject": row.subject,
            "delivery_status": row.delivery_status,
            "sent_at": row.sent_at,
        }
        for row in rows
    ]
