"""Auth API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from okbox.apps.auth.dependencies import get_current_user, require_role
from okbox.apps.auth.models import User, UserRole
from okbox.apps.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserCreateRequest,
    UserResponse,
)
from okbox.apps.auth.service import authenticate_user, create_user, refresh_access_token
from okbox.core.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Authenticate user and return JWT tokens."""
    return await authenticate_user(db, request)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Refresh access token using a valid refresh token."""
    return await refresh_access_token(db, request.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Get current user profile."""
    return current_user


@router.post("/users", response_model=UserResponse, status_code=201)
async def register_user(
    request: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> User:
    """Create a new user (admin only)."""
    return await create_user(db, request)
