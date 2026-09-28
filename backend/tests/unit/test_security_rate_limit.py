"""
GreenSynth Analytics — Security Rate Limiting Tests

Verifies that the rate limiting middleware and SlowAPI decorators:
1. Allow normal traffic within configured thresholds.
2. Intercept and block excessive requests with HTTP 429 Too Many Requests.
3. Return the standardized GreenSynth RATE_LIMIT_EXCEEDED JSON payload and Retry-After header.
4. Protect against brute-force password guessing.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.main import app
from app.api.deps import get_db


@pytest.mark.asyncio
async def test_auth_rate_limiting_enforcement(db_session: AsyncSession):
    """
    Test that rapid consecutive requests to the /api/v1/auth/login endpoint
    trigger a 429 Too Many Requests when rate limiting is enabled.
    """
    settings = get_settings()
    original_state = settings.rate_limit_enabled
    settings.rate_limit_enabled = True
    limiter.enabled = True

    # Override database session for test
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        # Reset limiter storage before test
        limiter.reset()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            responses = []
            # settings.rate_limit_auth_login is 10/minute by default
            # Send 12 rapid requests from the same test client IP
            for i in range(12):
                res = await client.post(
                    "/api/v1/auth/login",
                    json={"email": "attacker@example.com", "password": f"guess_{i}"},
                )
                responses.append(res)

            status_codes = [r.status_code for r in responses]

            # The initial requests should return 401 Unauthorized (invalid credentials)
            assert 401 in status_codes, f"Expected 401 in {status_codes}"

            # Once the rate limit threshold is hit, it must return 429 Too Many Requests
            assert 429 in status_codes, f"Expected 429 in {status_codes}"

            # Inspect the first 429 response
            throttled_response = next(r for r in responses if r.status_code == 429)
            body = throttled_response.json()

            assert body.get("error_code") == "RATE_LIMIT_EXCEEDED"
            assert "Rate limit exceeded" in body.get("message", "")
            assert "Retry-After" in throttled_response.headers
    finally:
        # Restore test settings state
        settings.rate_limit_enabled = original_state
        limiter.enabled = original_state
        limiter.reset()
        app.dependency_overrides.clear()
