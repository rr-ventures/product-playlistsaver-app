# Playlist Saver

Playlist Saver monitors Spotify and YouTube playlists, snapshots track lists, and emails you when tracks disappear.

## What is implemented

- FastAPI backend with Google and Spotify OAuth login
- JWT auth with httpOnly cookie sessions
- PostgreSQL models for users, playlists, tracks, removal events, subscriptions, and notification logs
- Playlist sync/check flow with track removal detection
- Celery worker + beat for daily scheduled checks
- Next.js frontend with login and dashboard playlist management
- Stripe routes wired but disabled by default (`PAYMENTS_ENABLED=false`)
- SoundCloud service placeholder (non-functional by design)

## Quick start

1. (Optional) refresh local env file from template:

   ```bash
   cp .env.example .env
   ```

2. Set required values in `.env`:
   - `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`
   - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
   - `JWT_SECRET_KEY`
   - `ENCRYPTION_KEY` (Fernet key)

   Generate a Fernet key:

   ```bash
   python3 - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
   ```

3. Configure OAuth redirect URLs in provider dashboards:
   - Spotify: `http://localhost:8000/api/auth/spotify/callback`
   - Google: `http://localhost:8000/api/auth/google/callback`

4. Run:

   ```bash
   docker compose up --build
   ```

5. Open:
   - Frontend: `http://localhost:3000`
   - API docs: `http://localhost:8000/docs`

## Notes

- Payments endpoints return validation/error responses while disabled.
- YouTube access uses Google OAuth with YouTube read scope.
- For local development cookie security is relaxed when `ENVIRONMENT=development`.
- API startup retries DB initialization to handle slow Postgres startup in Docker.
