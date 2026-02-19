from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models import PlaylistPlatform, SubscriptionTier


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    display_name: str | None
    avatar_url: str | None
    spotify_id: str | None
    google_id: str | None
    subscription_tier: SubscriptionTier
    created_at: datetime


class PlaylistCreate(BaseModel):
    platform: PlaylistPlatform
    platform_playlist_id: str
    name: str
    playlist_url: str
    is_public_monitor: bool = False


class PlaylistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    platform: PlaylistPlatform
    platform_playlist_id: str
    name: str
    playlist_url: str
    is_public_monitor: bool
    is_active: bool
    last_checked_at: datetime | None
    created_at: datetime


class TrackRemovalEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    playlist_id: UUID
    track_id: UUID
    detected_at: datetime
    notification_sent: bool
    notification_sent_at: datetime | None


class UserUpdate(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None
