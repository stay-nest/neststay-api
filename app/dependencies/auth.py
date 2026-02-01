"""Auth dependency for extracting current guest from JWT."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlmodel import Session

from app.models.guest import Guest
from app.services.guest_service import GuestService
from app.utils.jwt import decode_token
from database import get_session

# HTTPBearer: Swagger Authorize asks only for the access token.
# Get a token via POST /auth/login with JSON body { "email", "password" }.
http_bearer = HTTPBearer()


def get_current_guest(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    session: Session = Depends(get_session),
) -> Guest:
    """Dependency to extract guest from JWT. Raises 401 if invalid."""
    token = credentials.credentials
    try:
        payload = decode_token(token)
        guest_id = int(payload["sub"])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from None
    guest = GuestService(session).get_guest_by_id(guest_id)
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return guest
