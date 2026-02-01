"""Auth service for authentication and token handling."""

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.guest import Guest
from app.repositories.guest_repo import GuestRepository
from app.schemas.auth_schema import TokenResponse
from app.utils.jwt import create_access_token, create_refresh_token, decode_token
from app.utils.password import verify_password


class AuthService:
    """Service for authenticating guests and creating/refreshing tokens."""

    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
        self.guest_repo = GuestRepository(session)

    def authenticate(self, email: str, password: str) -> Guest:
        """Validate credentials, return guest or raise 401."""
        guest = self.guest_repo.get_guest_by_email(email)
        if not guest:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not guest.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not verify_password(password, guest.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        return guest

    def create_tokens(self, guest_id: int) -> TokenResponse:
        """Generate access + refresh token pair."""
        access_token = create_access_token(guest_id)
        refresh_token = create_refresh_token(guest_id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",  # noqa: S106
        )

    def refresh_access_token(self, refresh_token: str) -> str:
        """Validate refresh token, return new access token."""
        payload = decode_token(refresh_token)
        guest_id = int(payload["sub"])
        return create_access_token(guest_id)
