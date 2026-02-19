from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api.middleware import InMemoryRateLimiter
from app.api.routes import auth, payments, playlists, platforms, users
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
    allow_headers=["*"],
)
app.add_middleware(InMemoryRateLimiter)

app.include_router(auth.router)
app.include_router(playlists.router)
app.include_router(platforms.router)
app.include_router(users.router)
app.include_router(payments.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
