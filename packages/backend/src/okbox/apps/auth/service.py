"""Auth business logic."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from okbox.apps.auth.models import User, UserRole
from okbox.apps.auth.schemas import LoginRequest, TokenResponse, UserCreateRequest
from okbox.apps.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from okbox.core.config import settings
from okbox.core.exceptions import ForbiddenException, UnauthorizedException, ValidationException

# Lock account after N failed attempts
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


async def authenticate_user(db: AsyncSession, request: LoginRequest) -> TokenResponse:
    """Authenticate user and return tokens."""
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedException("Invalid username or password")

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise ForbiddenException("Account is locked. Try again later.")

    # Verify password
    if not verify_password(request.password, user.password_hash):
        user.login_attempts += 1
        if user.login_attempts >= MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=LOCKOUT_DURATION_MINUTES
            )
        await db.commit()
        raise UnauthorizedException("Invalid username or password")

    if not user.is_active:
        raise ForbiddenException("Account is disabled")

    # Reset login attempts on success
    user.login_attempts = 0
    user.locked_until = None
    await db.commit()

    # Generate tokens
    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
    """Refresh access token using a valid refresh token."""
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid token type")
    except Exception:
        raise UnauthorizedException("Invalid or expired refresh token")

    import uuid

    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise UnauthorizedException("User not found or inactive")

    access_token = create_access_token(user.id, user.role.value)
    new_refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


async def create_user(db: AsyncSession, request: UserCreateRequest) -> User:
    """Create a new user (admin only)."""
    # Check username uniqueness
    result = await db.execute(select(User).where(User.username == request.username))
    if result.scalar_one_or_none() is not None:
        raise ValidationException("Username already exists")

    user = User(
        username=request.username,
        display_name=request.display_name,
        password_hash=hash_password(request.password),
        role=request.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
