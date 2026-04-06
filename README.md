# Playlist Saver

A personal tool that monitors your Spotify and YouTube playlists, snapshots track lists over time, and alerts you when songs disappear.

## What It Does

Sign in with Spotify or Google, add playlists to monitor, and the app takes care of the rest. A daily Celery job checks every active playlist, compares the current track list against what was stored, and sends an email notification with details of any removed tracks.

All features are unlocked — unlimited playlists, manual on-demand checks, and public URL monitoring.

## Core Features

- **Spotify and YouTube OAuth** with encrypted token storage
- **Playlist discovery** from your connected accounts
- **Automated daily checks** via Celery Beat with track removal detection
- **Manual on-demand checks** for any monitored playlist
- **Email notifications** via Resend when tracks disappear
- **Dashboard** for managing monitored playlists and browsing platform libraries
- **Rate limiting middleware** for API safety
- **Public URL monitoring** — paste a playlist link and monitor it without OAuth

## What Is Implemented

| Feature | Status |
|---------|--------|
| Spotify OAuth, playlists, and track sync | Implemented |
| YouTube (Google) OAuth, playlists, and track sync | Implemented |
| Daily scheduled playlist checks | Implemented |
| Track removal detection and event logging | Implemented |
| Email notifications via Resend | Implemented |
| JWT auth with httpOnly cookies + refresh tokens | Implemented |
| CSRF protection (double-submit cookie) | Implemented |
| SoundCloud integration | Placeholder (returns disabled message) |

## Stack

**Backend**: FastAPI, SQLAlchemy (async), asyncpg, PostgreSQL, Celery, Redis, python-jose, cryptography, Resend

**Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS

**Infrastructure**: Docker Compose (Postgres, Redis, backend, worker, beat, frontend)

## Quick Start

1. Copy environment config:

```bash
cp .env.example .env
```

2. Set required values in `.env`:
   - `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`
   - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
   - `JWT_SECRET_KEY`
   - `ENCRYPTION_KEY` (generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)

3. Configure OAuth redirect URLs in provider dashboards:
   - Spotify: `http://localhost:8000/api/auth/spotify/callback`
   - Google: `http://localhost:8000/api/auth/google/callback`

4. Run:

```bash
docker compose up --build
```

5. Open:
   - Frontend: http://localhost:3000
   - API docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

## Security Configuration

### Secrets Management

All secrets are loaded from environment variables (`.env` file or container env). **Never commit real secrets to version control.**

| Variable | Purpose | How to Generate |
|----------|---------|-----------------|
| `JWT_SECRET_KEY` | Signs JWT access and refresh tokens | `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `ENCRYPTION_KEY` | Encrypts OAuth tokens at rest (Fernet) | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `SPOTIFY_CLIENT_SECRET` | Spotify OAuth | Spotify Developer Dashboard |
| `GOOGLE_CLIENT_SECRET` | Google OAuth | Google Cloud Console |
| `RESEND_API_KEY` | Email delivery | Resend dashboard |

**Production guard:** The app refuses to start in `ENVIRONMENT=production` if `JWT_SECRET_KEY` or `ENCRYPTION_KEY` are still set to their placeholder defaults.

### OAuth Token Encryption

OAuth access and refresh tokens from Spotify and Google are encrypted at rest using Fernet symmetric encryption before being stored in the database. If `ENCRYPTION_KEY` is not configured in development, a warning is logged and tokens are stored in plaintext. In production, the app will not start without a valid key.

### JWT Authentication

- **Access tokens** are short-lived (default 30 minutes, configurable via `JWT_ACCESS_EXPIRATION_MINUTES`)
- **Refresh tokens** are longer-lived (default 7 days, configurable via `JWT_REFRESH_EXPIRATION_DAYS`) and scoped to the `/api/auth/refresh` path
- Both tokens are stored in httpOnly cookies with `SameSite=Lax` and `Secure` flag in production
- Each token includes `iat` (issued at), `jti` (unique ID), and `type` claims
- The refresh endpoint issues a new access + refresh token pair (rotation)

### CSRF Protection

State-changing requests (`POST`, `PATCH`, `PUT`, `DELETE`) require a CSRF token via the double-submit cookie pattern:

1. On any `GET` request, a `csrf_token` cookie is set (readable by JavaScript)
2. State-changing requests must include the same value in the `X-CSRF-Token` header
3. OAuth callbacks are exempted

Frontend integration: read `csrf_token` from `document.cookie` and include it as the `X-CSRF-Token` header on all mutating API calls.

### Rate Limiting

An in-memory sliding-window rate limiter is applied to all endpoints:

- Default: 120 requests per 60 seconds per IP
- Returns `429 Too Many Requests` when exceeded
- Response headers `X-RateLimit-Limit` and `X-RateLimit-Remaining` are included
- Stale entries are cleaned up periodically to prevent memory leaks

### Health Check

`GET /health` returns the status of all dependencies:

```json
{
  "status": "ok",
  "database": "connected",
  "redis": "connected",
  "encryption_configured": true
}
```

The `status` field is `"ok"` when all services are reachable, `"degraded"` if any dependency check fails.

## Observability

### Structured Logging

- **Production**: JSON-line format (machine-parseable) written to stdout
- **Development**: Human-readable `timestamp level logger message` format
- Configured via `LOG_LEVEL` env var (default `INFO`)

### Celery Task Logging

All Celery tasks emit structured logs:

- **Task start**: task ID, timestamp
- **Task completion**: task ID, elapsed time, processed/failed/removed counts
- **Per-playlist failures**: playlist ID, name, platform, user ID, full stack trace
- **Task-level failures**: caught by Celery signal handler with exception details
- **Retries**: logged with reason and task ID

### Email Delivery Tracking

- Every email attempt is logged to the `notification_log` table with status (`sent`, `failed`, `skipped`)
- Resend provider message IDs are captured on successful sends
- Delivery failures are logged with full exception context
- The `/api/users/me/notifications` endpoint exposes delivery history

## Project Structure

```
backend/
  app/
    main.py                   FastAPI app with lifespan DB init
    config.py                 Settings from environment with production validation
    api/
      dependencies.py         JWT cookie auth
      middleware.py            Rate limiting + CSRF protection
      routes/                 auth, playlists, platforms, users
    database/session.py       Async SQLAlchemy engine
    models/entities.py        User, Playlist, Track, TrackRemovalEvent, NotificationLog
    services/
      playlist_manager.py     Sync and check logic
      spotify_service.py      Spotify OAuth and API
      youtube_service.py      YouTube OAuth and API
      soundcloud_service.py   Placeholder
      notification_service.py Email via Resend with delivery tracking
    tasks/
      celery_app.py           Celery config, beat schedule, failure signal handlers
      playlist_tasks.py       Daily check task with structured logging
    utils/                    JWT (access + refresh), encryption, structured logging
  tests/
frontend/
  src/
    app/
      page.tsx                Home with OAuth buttons
      dashboard/page.tsx      Playlist management
    lib/api.ts                API client
    components/               LogoutButton
docker-compose.yml            Postgres, Redis, backend, worker, beat, frontend
.github/workflows/ci.yml     pytest + npm lint/build
```
