class SoundCloudService:
    def not_available(self) -> dict[str, str]:
        return {
            "status": "placeholder",
            "message": "SoundCloud integration is intentionally disabled until API registration opens.",
        }
