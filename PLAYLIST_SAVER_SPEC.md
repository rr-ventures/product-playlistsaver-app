# Playlist Saver - Full Build Spec

## Executive Summary

Playlist Saver is a SaaS web app that monitors user playlists on YouTube and Spotify, stores compliance-safe snapshots, and sends email alerts when tracks are removed.

- Free tier: 1 monitored playlist
- Paid tier: unlimited playlists + public playlist URL monitoring
- Auth: Spotify OAuth + Google OAuth only
- Frequency: daily checks
- Notifications: email only
- Pricing: $4.99/month or $39.99/year
- SoundCloud: placeholder integration only (API registration blocked for new apps)

---

## Confirmed Technology Stack

- Backend: FastAPI (Python 3.12)
- DB: PostgreSQL 16
- ORM/Migrations: SQLAlchemy 2.0 + Alembic
- Background jobs: Celery + Redis
- Frontend: Next.js 14 + React 18 + TypeScript
- UI: Tailwind CSS (light, clean design)
- Payments: Stripe
- Notifications: pluggable email provider (default Resend)
- Repo strategy: monorepo
- Deployment baseline: Docker + compose, later Kubernetes-ready

---

## Compliance and ToS Notes (Research Summary)

### YouTube Data API
- No indefinite storage of API data.
- User data must be deletable on request.
- Must comply with YouTube API Services Terms and Developer Policies.
- Playlist monitoring is acceptable if consent, retention limits, and policy rules are followed.

### Spotify Web API
- Metadata cannot be offered as a standalone service.
- App must link back to Spotify content where appropriate.
- Must provide disconnect/account deletion paths.
- Extended quota access has stricter requirements from 2025 onward.

### SoundCloud API
- New API app registrations are currently closed.
- Implement only as placeholder service interface; no production integration without existing credentials.

### Compliance-safe data policy chosen
- Persist only minimal fields:
  - `platform_track_id`
  - `track_name`
  - `artist_name`
  - `position`
- Fetch rich metadata on demand instead of long-term storage.
- Keep attribution links to source platforms.

---

## Product Scope

### Core Features
- OAuth login with Spotify and Google (no username/password)
- Playlist monitoring (YouTube + Spotify)
- Detect removed tracks and notify users by email
- Subscription billing with Stripe
- Tier limits enforcement (free vs paid)
- Public playlist URL monitoring is paid-only

### Target Platform
- Web app only (mobile-optimized responsive UI)

---

## Monorepo Structure

```text
playlist-saver/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   │   ├── dependencies.py
│   │   │   ├── middleware.py
│   │   │   └── routes/
│   │   │       ├── auth.py
│   │   │       ├── playlists.py
│   │   │       ├── users.py
│   │   │       ├── payments.py
│   │   │       └── platforms.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── spotify_service.py
│   │   │   ├── youtube_service.py
│   │   │   ├── soundcloud_service.py
│   │   │   ├── playlist_manager.py
│   │   │   ├── notification_service.py
│   │   │   └── stripe_service.py
│   │   ├── tasks/
│   │   │   ├── celery_app.py
│   │   │   └── playlist_tasks.py
│   │   ├── database/
│   │   │   ├── session.py
│   │   │   └── migrations/
│   │   └── utils/
│   │       ├── encryption.py
│   │       ├── jwt.py
│   │       └── logging.py
│   ├── tests/
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── types/
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── Dockerfile
├── .devcontainer/
│   ├── devcontainer.json
│   ├── docker-compose.yml
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── .github/workflows/ci.yml
├── README.md
└── PLAYLIST_SAVER_SPEC.md
```

---

## Data Model (PostgreSQL)

### `users`
- `id` (uuid, pk)
- `email` (unique)
- `display_name`
- `avatar_url`
- `spotify_id` (nullable, unique)
- `google_id` (nullable, unique)
- encrypted OAuth tokens (access + refresh per provider)
- `subscription_tier` (`free`, `paid`)
- `stripe_customer_id`
- `created_at`, `updated_at`

### `subscriptions`
- `id` (uuid, pk)
- `user_id` (fk)
- `stripe_subscription_id` (unique)
- `plan` (`monthly`, `annual`)
- `status`
- `current_period_start`, `current_period_end`
- timestamps

### `playlists`
- `id` (uuid, pk)
- `user_id` (fk)
- `platform` (`spotify`, `youtube`)
- `platform_playlist_id`
- `name`
- `playlist_url`
- `is_public_monitor` (paid-only feature)
- `is_active`
- `last_checked_at`
- timestamps

### `tracks`
- `id` (uuid, pk)
- `playlist_id` (fk)
- `platform_track_id`
- `track_name`
- `artist_name`
- `position`
- `is_removed`
- `removed_at`
- `first_seen_at`
- `last_seen_at`

### `track_removal_events`
- `id` (uuid, pk)
- `playlist_id` (fk)
- `track_id` (fk)
- `detected_at`
- `notification_sent`
- `notification_sent_at`

### `notification_log`
- `id` (uuid, pk)
- `user_id` (fk)
- `event_type`
- `subject`
- `body`
- `delivery_status`
- `sent_at`

---

## API Endpoints

### Auth
- `GET /api/auth/spotify/login`
- `GET /api/auth/spotify/callback`
- `GET /api/auth/google/login`
- `GET /api/auth/google/callback`
- `POST /api/auth/logout`
- `GET /api/auth/me`

### Playlists
- `GET /api/playlists`
- `POST /api/playlists`
- `GET /api/playlists/{id}`
- `DELETE /api/playlists/{id}`
- `POST /api/playlists/{id}/check` (paid)
- `GET /api/playlists/{id}/history`

### Platform discovery
- `GET /api/platforms/spotify/playlists`
- `GET /api/platforms/youtube/playlists`
- `POST /api/platforms/resolve-url` (paid)

### Payments
- `POST /api/payments/checkout`
- `POST /api/payments/webhook`
- `GET /api/payments/subscription`
- `POST /api/payments/cancel`
- `POST /api/payments/portal`

### Users
- `GET /api/users/me`
- `PATCH /api/users/me`
- `DELETE /api/users/me`
- `GET /api/users/me/notifications`

---

## Tier Rules

### Free
- 1 monitored playlist max
- Daily checks
- Email notifications
- No public URL monitoring
- 30-day removal history

### Paid
- Unlimited monitored playlists
- Daily checks + manual check endpoint
- Public playlist URL monitoring
- Email notifications
- Unlimited removal history

---

## Monitoring and Event Flow

1. Celery Beat triggers daily job.
2. Worker iterates active playlists.
3. `playlist_manager` fetches current track list from platform service.
4. Compare snapshot vs current data by `platform_track_id`.
5. Mark missing tracks as removed.
6. Create `track_removal_events`.
7. Send email notification.
8. Write `notification_log`.

---

## Security and Reliability Requirements

- OAuth2 with secure state validation and PKCE where supported
- JWT in httpOnly secure cookies
- Encrypt provider tokens at rest
- Rate limiting middleware on API routes
- Input validation via Pydantic schemas
- Structured application logging via Python `logging`
- Idempotent Stripe webhook processing
- Soft-fail and retry logic for platform API outages

---

## Performance and Scalability KPIs

- API p95 latency < 300 ms for standard authenticated endpoints
- Playlist check worker throughput: process at least 5,000 playlists/hour/worker baseline
- Horizontal scaling:
  - API stateless and replicable
  - Multiple Celery workers
  - Redis/Postgres managed separately
- Error budget:
  - < 1% failed scheduled checks/day
  - < 0.1% failed webhook processing/day (with retry)

---

## Testing Requirements (>80% Coverage)

### Backend
- `pytest`, `pytest-asyncio`, `pytest-cov`
- Unit tests for services and utilities
- Integration tests for all API endpoints
- Webhook tests with signature validation
- Tier-limit and auth guard tests

### Frontend
- Jest + React Testing Library
- Component rendering and critical flows
- Auth and subscription state behavior tests

### Illustrative scenarios required
- Successful Spotify/Google login
- Track removal detection and notification send
- Successful paid subscription and cancellation
- Free-tier limit enforcement
- Edge cases:
  - private playlists
  - unavailable tracks by region
  - expired OAuth tokens with refresh

---

## CI/CD Requirements

GitHub Actions pipeline:
- Backend lint and format checks
- Frontend lint checks
- Type checks (mypy + TypeScript)
- Backend + frontend tests with coverage
- Docker build validation for frontend/backend images

---

## Environment Variables (baseline)

```env
ENVIRONMENT=development
LOG_LEVEL=INFO
APP_URL=http://localhost:3000
API_URL=http://localhost:8000

DATABASE_URL=postgresql+asyncpg://playlist_saver:playlist_saver@postgres:5432/playlist_saver
REDIS_URL=redis://redis:6379/0

JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
ENCRYPTION_KEY=replace-with-generated-fernet-key

SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
SPOTIFY_REDIRECT_URI=http://localhost:8000/api/auth/spotify/callback

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_MONTHLY=
STRIPE_PRICE_ANNUAL=

EMAIL_PROVIDER=resend
EMAIL_FROM=notifications@playlistsaver.local
RESEND_API_KEY=
```

---

## Build Order for Codex

1. Scaffold monorepo + configs + Docker/DevContainer
2. Build backend foundation (FastAPI app, settings, DB session)
3. Implement models + Alembic migrations
4. Implement OAuth + JWT auth
5. Implement platform services (Spotify/YouTube + SoundCloud placeholder)
6. Implement playlist endpoints + tier enforcement
7. Implement Celery scheduled checks + removal detection
8. Implement notification pipeline (email provider abstraction)
9. Implement Stripe checkout/subscription/webhooks
10. Build frontend pages, components, API integration
11. Add comprehensive tests to exceed 80% coverage
12. Add CI workflow, docs, and production-hardening notes

---

## Notes for Shipping

- SoundCloud remains a non-functional placeholder unless valid API credentials are available.
- Keep platform policy links in README compliance section and review quarterly.
- If future requirements add push notifications/mobile apps, design current services to remain transport-agnostic.

