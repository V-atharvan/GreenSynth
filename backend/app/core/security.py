"""
GreenSynth Analytics — Cryptographic Security & JWT Utilities

Handles:
  1. Secure password hashing & verification via bcrypt.
  2. One-way hashing for invitation onboarding tokens.
  3. JWT access token generation and verification.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

# Passlib CryptContext using PBKDF2-SHA256 (built-in NIST standard) with bcrypt support
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


class TokenDecodeError(Exception):
    """Raised when a JWT access token is malformed, expired, or invalid."""


def hash_password(password: str) -> str:
    """Generate a secure cryptographic bcrypt hash of the plain password."""
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string.")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its bcrypt hash in constant time."""
    if not plain_password or not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def generate_secure_invitation_token() -> str:
    """Generate a cryptographically secure, random URL-safe invitation token."""
    return secrets.token_urlsafe(32)


def hash_invitation_token(raw_token: str) -> str:
    """Hash an invitation token using SHA-256 for secure storage."""
    clean_token = raw_token.strip()
    return hashlib.sha256(clean_token.encode("utf-8")).hexdigest()


def create_access_token(
    user_id: uuid.UUID | str,
    account_type: str | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Generate a signed JWT access token for an authenticated user.

    Payload claims:
      - sub: User UUID string
      - type: 'access'
      - account_type: Optional authoritative account type ('ADMIN' or 'STUDENT')
      - iat: Issued at UTC timestamp
      - exp: Expiration UTC timestamp
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if account_type is not None:
        payload["account_type"] = account_type

    encoded_jwt = jwt.encode(
        payload, settings.secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Validates signature, algorithm, expiration, token type, and subject.
    Raises TokenDecodeError on any validation failure.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise TokenDecodeError(f"Invalid or expired token: {exc}") from exc

    if payload.get("type") != "access":
        raise TokenDecodeError("Token type is not access token.")

    sub = payload.get("sub")
    if not sub:
        raise TokenDecodeError("Token subject is missing.")

    try:
        uuid.UUID(str(sub))
    except (ValueError, AttributeError):
        raise TokenDecodeError("Token subject is not a valid UUID.")

    return payload
