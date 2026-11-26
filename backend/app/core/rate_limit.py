"""Lightweight in-memory sliding-window rate limiter for auth and Gemini endpoints."""

from __future__ import annotations

from collections import defaultdict, deque
import threading
import time
from fastapi import HTTPException, Request, status

_LOCK = threading.Lock()
_BUCKETS: dict[str, deque[float]] = defaultdict(deque)


def reset_rate_limits() -> None:
    """Clear rate-limit buckets (useful in test fixtures)."""
    with _LOCK:
        _BUCKETS.clear()


def rate_limit(scope: str, max_requests: int, window_seconds: int = 60):
    """Return a FastAPI dependency enforcing `max_requests` per `window_seconds`."""

    def _dependency(request: Request) -> None:
        client_host = request.client.host if request.client else "unknown"
        key = f"{scope}:{client_host}"
        now = time.monotonic()
        cutoff = now - window_seconds

        with _LOCK:
            bucket = _BUCKETS[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        f"Rate limit exceeded for {scope}. "
                        f"Try again in {window_seconds} seconds."
                    ),
                )
            bucket.append(now)

    return _dependency
