from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models import Playlist, TrackRemovalEvent, User
from app.schemas.common import PlaylistCreate, PlaylistOut, TrackRemovalEventOut
from app.services.playlist_manager import PlaylistManager

router = APIRouter(prefix="/api/playlists", tags=["playlists"])
manager = PlaylistManager()


@router.get("", response_model=list[PlaylistOut])
async def list_playlists(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    playlists = (await db.execute(select(Playlist).where(Playlist.user_id == current_user.id))).scalars().all()
    return [PlaylistOut.model_validate(p) for p in playlists]


@router.post("", response_model=PlaylistOut)
async def create_playlist(
    payload: PlaylistCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    playlist = Playlist(user_id=current_user.id, **payload.model_dump())
    db.add(playlist)
    await db.commit()
    await db.refresh(playlist)
    return PlaylistOut.model_validate(playlist)


@router.get("/{playlist_id}", response_model=PlaylistOut)
async def get_playlist(playlist_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    playlist = await db.scalar(select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id))
    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")
    return PlaylistOut.model_validate(playlist)


@router.delete("/{playlist_id}")
async def delete_playlist(
    playlist_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    playlist = await db.scalar(select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id))
    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")
    await db.delete(playlist)
    await db.commit()
    return {"message": "Playlist deleted"}


@router.post("/{playlist_id}/check")
async def manual_check(playlist_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    playlist = await db.scalar(select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id))
    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")
    return await manager.check_playlist(db, playlist, current_user)


@router.get("/{playlist_id}/history", response_model=list[TrackRemovalEventOut])
async def history(playlist_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    playlist = await db.scalar(select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id))
    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")
    events = (
        await db.execute(select(TrackRemovalEvent).where(TrackRemovalEvent.playlist_id == playlist.id))
    ).scalars().all()
    return [TrackRemovalEventOut.model_validate(e) for e in events]
