from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl

from app.api.dependencies import get_current_user
from app.models import User
from app.services.soundcloud_service import SoundCloudService
from app.services.spotify_service import SpotifyService
from app.services.youtube_service import YouTubeService
from app.utils.encryption import decrypt_value

router = APIRouter(prefix="/api/platforms", tags=["platforms"])
spotify_service = SpotifyService()
youtube_service = YouTubeService()
soundcloud_service = SoundCloudService()


@router.get("/spotify/playlists")
async def spotify_playlists(current_user: User = Depends(get_current_user)):
    token = decrypt_value(current_user.spotify_access_token)
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Connect Spotify first")
    return await spotify_service.list_playlists(token)


@router.get("/youtube/playlists")
async def youtube_playlists(current_user: User = Depends(get_current_user)):
    token = decrypt_value(current_user.google_access_token)
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Connect Google/YouTube first")
    return await youtube_service.list_playlists(token)


class ResolveUrlRequest(BaseModel):
    url: HttpUrl


@router.post("/resolve-url")
async def resolve_url(payload: ResolveUrlRequest, current_user: User = Depends(get_current_user)):
    url = str(payload.url)
    if "spotify.com/playlist/" in url:
        playlist_id = url.split("playlist/")[-1].split("?")[0]
        return {"platform": "spotify", "platform_playlist_id": playlist_id, "playlist_url": url}
    if "youtube.com/playlist" in url and "list=" in url:
        playlist_id = url.split("list=")[-1].split("&")[0]
        return {"platform": "youtube", "platform_playlist_id": playlist_id, "playlist_url": url}
    if "soundcloud.com" in url:
        return soundcloud_service.not_available()
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported playlist URL")
