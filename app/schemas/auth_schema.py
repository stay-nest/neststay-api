"""Auth schemas for login, refresh, and token responses."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Login request body."""

    email: str
    password: str


class TokenResponse(BaseModel):
    """Token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105


class RefreshRequest(BaseModel):
    """Refresh token request body."""

    refresh_token: str
