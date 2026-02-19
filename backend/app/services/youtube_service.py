from typing import Any

import httpx


class YouTubeService:
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    PROFILE_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    PLAYLISTS_URL = "https://www.googleapis.com/youtube/v3/playlists"
    PLAYLIST_ITEMS_URL = "https://www.googleapis.com/youtube/v3/playlistItems"

    async def exchange_code(
        self, code: str, client_id: str, client_secret: str, redirect_uri: str
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_profile(self, access_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self.PROFILE_URL, headers={"Authorization": f"Bearer {access_token}"})
            response.raise_for_status()
            return response.json()

    async def list_playlists(self, access_token: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                self.PLAYLISTS_URL,
                params={"part": "snippet", "mine": "true", "maxResults": 50},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            payload = response.json()
            return [
                {
                    "id": item["id"],
                    "name": item["snippet"]["title"],
                    "url": f"https://www.youtube.com/playlist?list={item['id']}",
                }
                for item in payload.get("items", [])
            ]

    async def get_playlist_tracks(self, playlist_id: str, access_token: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                self.PLAYLIST_ITEMS_URL,
                params={"part": "snippet", "playlistId": playlist_id, "maxResults": 50},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            items = response.json().get("items", [])
            tracks: list[dict[str, Any]] = []
            for idx, item in enumerate(items):
                snippet = item.get("snippet", {})
                resource = snippet.get("resourceId", {})
                tracks.append(
                    {
                        "platform_track_id": resource.get("videoId", f"unknown-{idx}"),
                        "track_name": snippet.get("title", "Unknown Video"),
                        "artist_name": snippet.get("videoOwnerChannelTitle", "Unknown Channel"),
                        "position": idx,
                    }
                )
            return tracks
