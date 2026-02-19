import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware


class InMemoryRateLimiter(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 120, period_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.period_seconds = period_seconds
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        key = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = self.hits[key]
        while bucket and now - bucket[0] > self.period_seconds:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        bucket.append(now)
        return await call_next(request)
