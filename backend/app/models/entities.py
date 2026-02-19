import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PAID = "paid"


class PlaylistPlatform(str, enum.Enum):
    SPOTIFY = "spotify"
    YOUTUBE = "youtube"


class SubscriptionPlan(str, enum.Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(1024))
    spotify_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True)

    spotify_access_token: Mapped[str | None] = mapped_column(Text)
    spotify_refresh_token: Mapped[str | None] = mapped_column(Text)
    google_access_token: Mapped[str | None] = mapped_column(Text)
    google_refresh_token: Mapped[str | None] = mapped_column(Text)

    subscription_tier: Mapped[SubscriptionTier] = mapped_column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))

    playlists: Mapped[list["Playlist"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Subscription(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stripe_subscription_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    plan: Mapped[SubscriptionPlan] = mapped_column(Enum(SubscriptionPlan), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Playlist(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "playlists"
    __table_args__ = (UniqueConstraint("platform", "platform_playlist_id", name="uq_playlist_platform_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[PlaylistPlatform] = mapped_column(Enum(PlaylistPlatform), nullable=False)
    platform_playlist_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    playlist_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_public_monitor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="playlists")
    tracks: Mapped[list["Track"]] = relationship(back_populates="playlist", cascade="all, delete-orphan")


class Track(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "tracks"
    __table_args__ = (UniqueConstraint("playlist_id", "platform_track_id", name="uq_playlist_track_platform"),)

    playlist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False)
    platform_track_id: Mapped[str] = mapped_column(String(255), nullable=False)
    track_name: Mapped[str] = mapped_column(String(255), nullable=False)
    artist_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    is_removed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    playlist: Mapped[Playlist] = relationship(back_populates="tracks")


class TrackRemovalEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "track_removal_events"

    playlist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False)
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notification_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NotificationLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "notification_log"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    delivery_status: Mapped[str] = mapped_column(String(64), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
