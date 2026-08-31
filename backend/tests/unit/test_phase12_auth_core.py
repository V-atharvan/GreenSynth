"""
GreenSynth Analytics — Phase 12 Authentication Core Tests

Validates:
1. Password hashing, salt randomness, and verification.
2. JWT generation, decoding, expiration enforcement, and signature validation.
3. get_current_user resolution, bearer header validation, and inactive user rejection.
4. Email normalization (whitespace trimming, case-insensitivity).
5. Generic login failure consistency (no account enumeration).
6. Zero password/hash/secret exposure in schemas and endpoint responses.
7. /auth/me and /auth/logout endpoint contracts.
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

import app.models  # noqa: F401
from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.core.security import (
    TokenDecodeError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.main import app
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, TokenResponse, UserProfile, UserRead
from app.services.auth_service import AuthService


# ── FIXTURES ─────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def auth_test_users(db_session: AsyncSession):
    """Creates isolated active admin, active student, and inactive student accounts."""
    suffix = uuid.uuid4().hex[:6]

    admin = User(
        id=uuid.uuid4(),
        username=f"admin_{suffix}",
        email=f"admin_{suffix}@greensynth.edu",
        full_name="Administrator",
        department="Central Lab",
        phone="1234567890",
        roll_number=f"ADM-{suffix}",
        role=UserRole.ADMIN,
        password_hash=hash_password("admin_secret_pass"),
        is_active=True,
    )
    student_active = User(
        id=uuid.uuid4(),
        username=f"student_act_{suffix}",
        email=f"student_act_{suffix}@greensynth.edu",
        full_name="Active Student",
        department="Chemistry",
        phone="1234567891",
        roll_number=f"STU-ACT-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("student_secret_pass"),
        is_active=True,
    )
    student_inactive = User(
        id=uuid.uuid4(),
        username=f"student_inact_{suffix}",
        email=f"student_inact_{suffix}@greensynth.edu",
        full_name="Inactive Student",
        department="Physics",
        phone="1234567892",
        roll_number=f"STU-INACT-{suffix}",
        role=UserRole.RESEARCHER,
        password_hash=hash_password("inactive_secret_pass"),
        is_active=False,
    )
    db_session.add_all([admin, student_active, student_inactive])
    await db_session.flush()

    return {
        "admin": admin,
        "student_active": student_active,
        "student_inactive": student_inactive,
    }


def make_client(db_session: AsyncSession, token: str | None = None) -> AsyncClient:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=headers,
        follow_redirects=True,
    )


# ── 1. PASSWORD HASHING & VERIFICATION ───────────────────────────────

def test_password_hashing_and_verification():
    """Verifies password hashing is one-way, salted, and verifies correctly."""
    plain = "SuperSecurePassword123!"
    h1 = hash_password(plain)
    h2 = hash_password(plain)

    # 1. Hashes are non-empty strings
    assert isinstance(h1, str) and len(h1) > 20
    # 2. Hash is different from plaintext
    assert h1 != plain
    # 3. Repeated hashing produces unique salts
    assert h1 != h2
    # 4. Correct password verifies
    assert verify_password(plain, h1) is True
    assert verify_password(plain, h2) is True
    # 5. Incorrect password fails
    assert verify_password("WrongPassword123!", h1) is False
    assert verify_password("", h1) is False
    # 6. Plaintext not plainly contained in hash
    assert plain not in h1


def test_password_hashing_invalid_inputs():
    """Verifies error handling on empty or non-string inputs."""
    with pytest.raises(ValueError):
        hash_password("")
    with pytest.raises(ValueError):
        hash_password(None)  # type: ignore[arg-type]

    assert verify_password("", "some_hash") is False
    assert verify_password("pass", "") is False
    assert verify_password("pass", "malformed_hash") is False


# ── 2. JWT TOKEN CREATION, DECODING & EXPIRATION ──────────────────────

def test_jwt_generation_and_decoding():
    """Verifies JWT creation with sub, type, account_type, and expiration."""
    user_id = uuid.uuid4()
    token = create_access_token(user_id=user_id, account_type="ADMIN")

    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    assert payload["account_type"] == "ADMIN"
    assert "exp" in payload
    assert "iat" in payload
    assert payload["exp"] > payload["iat"]


def test_jwt_expiration_rejection():
    """Verifies expired JWT tokens are rejected with TokenDecodeError."""
    user_id = uuid.uuid4()
    expired_token = create_access_token(
        user_id=user_id,
        expires_delta=timedelta(seconds=-10),  # expired 10 seconds ago
    )

    with pytest.raises(TokenDecodeError) as exc_info:
        decode_access_token(expired_token)
    assert "expired" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()


def test_jwt_invalid_signature_rejection():
    """Verifies JWT with tampered signature is rejected."""
    settings = get_settings()
    user_id = uuid.uuid4()
    # Sign with a completely different rogue secret
    rogue_token = jwt.encode(
        {"sub": str(user_id), "type": "access", "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
        "rogue-secret-key-123",
        algorithm="HS256",
    )

    with pytest.raises(TokenDecodeError):
        decode_access_token(rogue_token)


def test_jwt_malformed_and_missing_claims():
    """Verifies malformed tokens and missing required claims raise TokenDecodeError."""
    settings = get_settings()

    # Malformed garbage string
    with pytest.raises(TokenDecodeError):
        decode_access_token("this.is.not.a.valid.jwt")

    # Missing sub claim
    token_no_sub = jwt.encode(
        {"type": "access", "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(TokenDecodeError):
        decode_access_token(token_no_sub)

    # Invalid non-UUID sub claim
    token_bad_sub = jwt.encode(
        {"sub": "not-a-uuid", "type": "access", "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(TokenDecodeError):
        decode_access_token(token_bad_sub)

    # Wrong token type
    token_wrong_type = jwt.encode(
        {"sub": str(uuid.uuid4()), "type": "refresh", "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(TokenDecodeError):
        decode_access_token(token_wrong_type)


# ── 3. GET_CURRENT_USER DEPENDENCY & ACTIVE STATUS ────────────────────

@pytest.mark.asyncio
async def test_get_current_user_success(db_session: AsyncSession, auth_test_users):
    """Verifies active admin and active student resolve successfully."""
    admin = auth_test_users["admin"]
    student = auth_test_users["student_active"]

    admin_token = create_access_token(admin.id, account_type=admin.account_type)
    student_token = create_access_token(student.id, account_type=student.account_type)

    admin_resolved = await get_current_user(
        auth_credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=admin_token),
        db=db_session,
    )
    assert admin_resolved.id == admin.id
    assert admin_resolved.account_type == "ADMIN"
    assert admin_resolved.is_admin is True

    student_resolved = await get_current_user(
        auth_credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=student_token),
        db=db_session,
    )
    assert student_resolved.id == student.id
    assert student_resolved.account_type == "STUDENT"
    assert student_resolved.is_admin is False


@pytest.mark.asyncio
async def test_get_current_user_inactive_user_rejected(db_session: AsyncSession, auth_test_users):
    """Verifies deactivated user with valid JWT is rejected with HTTP 401."""
    inactive_user = auth_test_users["student_inactive"]
    token = create_access_token(inactive_user.id, account_type=inactive_user.account_type)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            auth_credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
            db=db_session,
        )
    assert exc_info.value.status_code == 401
    assert "deactivated" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_get_current_user_unknown_user_rejected(db_session: AsyncSession):
    """Verifies JWT containing a non-existent user UUID is rejected with HTTP 401."""
    random_id = uuid.uuid4()
    token = create_access_token(random_id)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            auth_credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
            db=db_session,
        )
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_missing_credentials(db_session: AsyncSession):
    """Verifies missing credentials raises HTTP 401."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(auth_credentials=None, db=db_session)
    assert exc_info.value.status_code == 401


# ── 4. EMAIL NORMALIZATION & AUTHENTICATION SERVICE ──────────────────

@pytest.mark.asyncio
async def test_email_normalization_login(db_session: AsyncSession, auth_test_users):
    """Verifies emails with leading/trailing spaces and uppercase characters authenticate."""
    student = auth_test_users["student_active"]
    service = AuthService(db_session)

    # Original email
    r1 = await service.authenticate_user(LoginRequest(email=student.email, password="student_secret_pass"))
    assert r1.user.id == student.id

    # Uppercase email
    r2 = await service.authenticate_user(LoginRequest(email=student.email.upper(), password="student_secret_pass"))
    assert r2.user.id == student.id

    # Whitespace padded email
    r3 = await service.authenticate_user(LoginRequest(email=f"  {student.email}  ", password="student_secret_pass"))
    assert r3.user.id == student.id


@pytest.mark.asyncio
async def test_generic_login_failure(db_session: AsyncSession, auth_test_users):
    """Verifies invalid email and invalid password return identical generic 401 errors."""
    student = auth_test_users["student_active"]
    service = AuthService(db_session)

    # 1. Non-existent email
    with pytest.raises(HTTPException) as exc_wrong_email:
        await service.authenticate_user(LoginRequest(email="nonexistent@greensynth.edu", password="anypassword"))
    assert exc_wrong_email.value.status_code == 401
    assert exc_wrong_email.value.detail == "Invalid email or password"

    # 2. Existing email with incorrect password
    with pytest.raises(HTTPException) as exc_wrong_pass:
        await service.authenticate_user(LoginRequest(email=student.email, password="completely_wrong_pass"))
    assert exc_wrong_pass.value.status_code == 401
    assert exc_wrong_pass.value.detail == "Invalid email or password"


# ── 5. ZERO PASSWORD / HASH / SECRET EXPOSURE ────────────────────────

def test_pydantic_schemas_do_not_expose_password_hash():
    """Verifies UserRead and UserProfile schemas strictly exclude password_hash."""
    user_read_fields = UserRead.model_fields.keys()
    assert "password_hash" not in user_read_fields
    assert "password" not in user_read_fields

    user_profile_fields = UserProfile.model_fields.keys()
    assert "password_hash" not in user_profile_fields
    assert "password" not in user_profile_fields


@pytest.mark.asyncio
async def test_auth_me_and_login_do_not_expose_hash(db_session: AsyncSession, auth_test_users):
    """Verifies API endpoints never return password_hash in JSON responses."""
    student = auth_test_users["student_active"]
    token = create_access_token(student.id, account_type=student.account_type)

    async with make_client(db_session, token=token) as ac:
        # Check GET /api/v1/auth/me
        me_res = await ac.get("/api/v1/auth/me")
        assert me_res.status_code == 200
        me_text = me_res.text
        assert "password_hash" not in me_text
        assert student.password_hash not in me_text

        # Check POST /api/v1/auth/login
        login_res = await ac.post("/api/v1/auth/login", json={"email": student.email, "password": "student_secret_pass"})
        assert login_res.status_code == 200
        login_text = login_res.text
        assert "password_hash" not in login_text
        assert student.password_hash not in login_text


# ── 6. LOGOUT ENDPOINT & CONTRACT ────────────────────────────────────

@pytest.mark.asyncio
async def test_auth_logout_endpoint(db_session: AsyncSession, auth_test_users):
    """Verifies POST /api/v1/auth/logout succeeds with valid token and fails without."""
    student = auth_test_users["student_active"]
    token = create_access_token(student.id, account_type=student.account_type)

    # Authenticated logout
    async with make_client(db_session, token=token) as ac:
        res = await ac.post("/api/v1/auth/logout")
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "logged_out"

    # Unauthenticated logout
    async with make_client(db_session) as ac:
        res_unauth = await ac.post("/api/v1/auth/logout")
        assert res_unauth.status_code == 401
