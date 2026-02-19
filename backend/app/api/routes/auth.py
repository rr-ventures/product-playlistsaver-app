import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models import User
from app.schemas.common import UserOut
from app.services.spotify_service import SpotifyService
from app.services.youtube_service import YouTubeService
from app.utils.encryption import encrypt_value
from app.utils.jwt import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()
spotify_service = SpotifyService()
youtube_service = YouTubeService()


def _cookie_secure() -> bool:
    return settings.environment == "production"


@router.get("/spotify/login")
async def spotify_login() -> RedirectResponse:
    if not settings.spotify_client_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Spotify is not configured")

    state = secrets.token_urlsafe(24)
    query = urlencode(
        {
            "client_id": settings.spotify_client_id,
            "response_type": "code",
            "redirect_uri": settings.spotify_redirect_uri,
            "scope": "user-read-email playlist-read-private playlist-read-collaborative",
            "state": state,
            "show_dialog": "true",
        }
    )
    response = RedirectResponse(url=f"{SpotifyService.AUTH_URL}?{query}")
    response.set_cookie("spotify_oauth_state", state, httponly=True, secure=_cookie_secure(), samesite="lax")
    return response


@router.get("/spotify/callback")
async def spotify_callback(
    code: str = Query(...),
    state: str = Query(...),
    spotify_oauth_state: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if state != spotify_oauth_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    tokens = await spotify_service.exchange_code(
        code=code,
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        redirect_uri=settings.spotify_redirect_uri,
    )
    profile = await spotify_service.get_profile(tokens["access_token"])

    user = await db.scalar(select(User).where(User.email == profile["email"]))
    if not user:
        user = User(email=profile["email"])
        db.add(user)

    user.display_name = profile.get("display_name")
    user.avatar_url = (profile.get("images") or [{}])[0].get("url")
    user.spotify_id = profile.get("id")
    user.spotify_access_token = encrypt_value(tokens.get("access_token"))
    user.spotify_refresh_token = encrypt_value(tokens.get("refresh_token"))
    await db.commit()
    await db.refresh(user)

    jwt_token = create_access_token({"sub": str(user.id)})
    response = RedirectResponse(url=f"{settings.app_url}/dashboard")
    response.set_cookie("access_token", jwt_token, httponly=True, secure=_cookie_secure(), samesite="lax")
    response.delete_cookie("spotify_oauth_state")
    return response


@router.get("/google/login")
async def google_login() -> RedirectResponse:
    if not settings.google_client_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Google is not configured")

    state = secrets.token_urlsafe(24)
    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile https://www.googleapis.com/auth/youtube.readonly",
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
    )
    response = RedirectResponse(url=f"https://accounts.google.com/o/oauth2/v2/auth?{query}")
    response.set_cookie("google_oauth_state", state, httponly=True, secure=_cookie_secure(), samesite="lax")
    return response


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    google_oauth_state: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if state != google_oauth_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    tokens = await youtube_service.exchange_code(
        code=code,
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        redirect_uri=settings.google_redirect_uri,
    )
    profile = await youtube_service.get_profile(tokens["access_token"])

    user = await db.scalar(select(User).where(User.email == profile["email"]))
    if not user:
        user = User(email=profile["email"])
        db.add(user)

    user.display_name = profile.get("name")
    user.avatar_url = profile.get("picture")
    user.google_id = profile.get("id")
    user.google_access_token = encrypt_value(tokens.get("access_token"))
    user.google_refresh_token = encrypt_value(tokens.get("refresh_token"))
    await db.commit()
    await db.refresh(user)

    jwt_token = create_access_token({"sub": str(user.id)})
    response = RedirectResponse(url=f"{settings.app_url}/dashboard")
    response.set_cookie("access_token", jwt_token, httponly=True, secure=_cookie_secure(), samesite="lax")
    response.delete_cookie("google_oauth_state")
    return response


@router.post("/logout")
async def logout() -> Response:
    response = Response()
    response.delete_cookie("access_token")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)
