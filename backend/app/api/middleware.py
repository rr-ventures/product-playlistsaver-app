import hashlib
import hmac
import logging
import secrets
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

logger = logging.getLogger("playlist_saver.middleware")

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_CSRF_EXEMPT_PREFIXES = ("/api/auth/spotify/callback", "/api/auth/google/callback")
_CSRF_COOKIE = "csrf_token"
_CSRF_HEADER = "x-csrf-token"


class InMemoryRateLimiter(BaseHTTPMiddleware):
    """Sliding-window rate limiter with periodic cleanup of stale entries."""

    def __init__(self, app, max_requests: int = 120, period_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.period_seconds = period_seconds
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self._last_cleanup = time.time()
        self._cleanup_interval = 300

    def _cleanup_stale(self, now: float) -> None:
        if now - self._last_cleanup < self._cleanup_interval:
            return
        stale_keys = [k for k, v in self.hits.items() if not v or now - v[-1] > self.period_seconds]
        for key in stale_keys:
            del self.hits[key]
        self._last_cleanup = now

    async def dispatch(self, request: Request, call_next):
        key = request.client.host if request.client else "unknown"
        now = time.time()

        self._cleanup_stale(now)

        bucket = self.hits[key]
        while bucket and now - bucket[0] > self.period_seconds:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            logger.warning("Rate limit exceeded for %s", key)
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        bucket.append(now)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.max_requests - len(bucket)))
        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF protection for state-changing requests.

    GET/HEAD/OPTIONS are safe and skip validation. OAuth callbacks and
    webhooks are exempted since they don't carry the session cookie or
    come from trusted origins.
    """

    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()

    def _generate_token(self) -> str:
        return secrets.token_urlsafe(32)

    def _tokens_match(self, cookie_val: str, header_val: str) -> bool:
        return hmac.compare_digest(cookie_val, header_val)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method in _SAFE_METHODS:
            response = await call_next(request)
            self._ensure_csrf_cookie(request, response)
            return response

        if any(request.url.path.startswith(prefix) for prefix in _CSRF_EXEMPT_PREFIXES):
            return await call_next(request)

        cookie_token = request.cookies.get(_CSRF_COOKIE)
        header_token = request.headers.get(_CSRF_HEADER)

        if not cookie_token or not header_token or not self._tokens_match(cookie_token, header_token):
            raise HTTPException(status_code=403, detail="CSRF validation failed")

        response = await call_next(request)
        return response

    def _ensure_csrf_cookie(self, request: Request, response: Response) -> None:
        if _CSRF_COOKIE not in request.cookies:
            token = self._generate_token()
            is_prod = self.settings.environment == "production"
            response.set_cookie(
                _CSRF_COOKIE, token,
                httponly=False,  # JS must read this
                secure=is_prod,
                samesite="lax",
                max_age=86400,
            )
