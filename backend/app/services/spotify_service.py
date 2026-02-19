import base64
from typing import Any

import httpx


class SpotifyService:
    AUTH_URL = "https://accounts.spotify.com/authorize"
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    ME_URL = "https://api.spotify.com/v1/me"
    PLAYLISTS_URL = "https://api.spotify.com/v1/me/playlists"

    async def exchange_code(
        self, code: str, client_id: str, client_secret: str, redirect_uri: str
    ) -> dict[str, Any]:
        basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.TOKEN_URL,
                data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
                headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return response.json()

    async def get_profile(self, access_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self.ME_URL, headers={"Authorization": f"Bearer {access_token}"})
            response.raise_for_status()
            return response.json()

    async def list_playlists(self, access_token: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self.PLAYLISTS_URL, headers={"Authorization": f"Bearer {access_token}"})
            response.raise_for_status()
            payload = response.json()
            return [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "url": item["external_urls"]["spotify"],
                }
                for item in payload.get("items", [])
            ]

    async def get_playlist_tracks(self, playlist_id: str, access_token: str) -> list[dict[str, Any]]:
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers={"Authorization": f"Bearer {access_token}"})
            response.raise_for_status()
            items = response.json().get("items", [])
            tracks: list[dict[str, Any]] = []
            for idx, item in enumerate(items):
                track = item.get("track") or {}
                artists = track.get("artists") or []
                artist_name = artists[0]["name"] if artists else "Unknown Artist"
                tracks.append(
                    {
                        "platform_track_id": track.get("id", f"unknown-{idx}"),
                        "track_name": track.get("name", "Unknown Track"),
                        "artist_name": artist_name,
                        "position": idx,
                    }
                )
            return tracks
