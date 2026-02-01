"""Auth routes for login, refresh, and current user."""

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlmodel import Session

from app.dependencies.auth import get_current_guest
from app.models.guest import Guest
from app.schemas.auth_schema import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.guest_schema import GuestRead
from app.services.auth_service import AuthService
from database import get_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """Authenticate with email and password, return access and refresh tokens."""
    service = AuthService(session)
    guest = service.authenticate(data.email, data.password)
    return service.create_tokens(guest.id)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    data: RefreshRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """Exchange refresh token for new access token."""
    service = AuthService(session)
    try:
        new_access_token = service.refresh_access_token(data.refresh_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from None
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=data.refresh_token,
        token_type="bearer",  # noqa: S106
    )


@router.get("/me", response_model=GuestRead)
def get_me(current_guest: Guest = Depends(get_current_guest)) -> GuestRead:
    """Get current authenticated guest."""
    return GuestRead.model_validate(current_guest)
