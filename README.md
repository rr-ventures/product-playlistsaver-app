# Playlist Saver

Monitors Spotify and YouTube playlists, snapshots track lists over time, and alerts you when songs disappear.

## What It Does

You sign in with Spotify or Google, add playlists to monitor, and the app takes care of the rest. A daily Celery job checks every active playlist, compares the current track list against what was stored, and sends an email notification with details of any removed tracks.

Free tier gives you one monitored playlist. Paid tier (billing foundations are wired but currently disabled) unlocks more playlists, manual on-demand checks, and public URL monitoring.

## Core Features

- **Spotify and YouTube OAuth** with encrypted token storage
- **Playlist discovery** from your connected accounts
- **Automated daily checks** via Celery Beat with track removal detection
- **Email notifications** via Resend when tracks disappear
- **Dashboard** for managing monitored playlists and viewing platform libraries
- **Tier-based access control** with free and paid plan logic
- **Rate limiting middleware** built into the API

## What Is Implemented

| Feature | Status |
|---------|--------|
| Spotify OAuth, playlists, and track sync | Implemented |
| YouTube (Google) OAuth, playlists, and track sync | Implemented |
| Daily scheduled playlist checks | Implemented |
| Track removal detection and event logging | Implemented |
| Email notifications via Resend | Implemented |
| JWT auth with httpOnly cookies | Implemented |
| Free/paid tier logic | Implemented |
| SoundCloud integration | Placeholder (returns disabled message) |
| Stripe payments | Routes exist, disabled by default |

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

## Project Structure

```
backend/
  app/
    main.py                   FastAPI app with lifespan DB init
    config.py                 Settings from environment
    api/
      dependencies.py         JWT cookie auth
      middleware.py            Rate limiting
      routes/                 auth, playlists, platforms, users, payments
    database/session.py       Async SQLAlchemy engine
    models/entities.py        User, Subscription, Playlist, Track, TrackRemovalEvent, NotificationLog
    services/
      playlist_manager.py     Sync and check logic
      spotify_service.py      Spotify OAuth and API
      youtube_service.py      YouTube OAuth and API
      soundcloud_service.py   Placeholder
      stripe_service.py       Payment guard
      notification_service.py Email via Resend
    tasks/
      celery_app.py           Celery config and beat schedule
      playlist_tasks.py       Daily check task
    utils/                    JWT, encryption, logging
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
