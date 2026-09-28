"""
GreenSynth Analytics — Rate Limiting Infrastructure

Protects authentication and compute endpoints from brute-force attacks,
credential stuffing, and denial-of-service attempts.
"""

from __future__ import annotations

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_real_client_ip(request: Request) -> str:
    """
    Resolves client IP address, handling X-Forwarded-For and X-Real-IP headers
    from reverse proxies (Render, Vercel, Cloudflare, etc.).
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # First IP in the comma-separated list is the original client
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_real_client_ip,
    default_limits=[settings.rate_limit_default],
    enabled=settings.rate_limit_enabled,
    storage_uri="memory://",
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Standardized JSON response for HTTP 429 Too Many Requests.
    Follows GreenSynth error payload conventions.
    """
    client_ip = get_real_client_ip(request)
    logger.warning("Rate limit exceeded for client %s on %s: %s", client_ip, request.url.path, exc.detail)

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": f"Rate limit exceeded: {exc.detail}. Please try again later.",
        },
        headers={"Retry-After": "60"},
    )
