from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.middleware import CSRFMiddleware, InMemoryRateLimiter
from app.api.routes import auth, playlists, platforms, users
from app.config import get_settings
from app.database.session import engine
from app.models import Base
from app.utils.logging import configure_logging

settings = get_settings()
logger = logging.getLogger("playlist_saver.startup")


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    if not settings.skip_db_init:
        last_exc: Exception | None = None
        for attempt in range(1, settings.db_init_max_retries + 1):
            try:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                last_exc = None
                break
            except SQLAlchemyError as exc:
                last_exc = exc
                logger.warning("DB init attempt %s/%s failed: %s", attempt, settings.db_init_max_retries, exc)
                await asyncio.sleep(settings.db_init_retry_seconds)
        if last_exc is not None:
            raise last_exc
    yield


app = FastAPI(title="Playlist Saver API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.app_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "x-csrf-token"],
)
app.add_middleware(CSRFMiddleware)
app.add_middleware(InMemoryRateLimiter)

app.include_router(auth.router)
app.include_router(playlists.router)
app.include_router(platforms.router)
app.include_router(users.router)


@app.get("/health")
async def health() -> dict:
    checks: dict = {"status": "ok"}

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as exc:
        checks["database"] = f"error: {exc}"
        checks["status"] = "degraded"

    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        checks["redis"] = "connected"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"
        checks["status"] = "degraded"

    checks["encryption_configured"] = not settings.encryption_key.startswith("replace-with")

    return checks
