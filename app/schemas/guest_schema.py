"""Guest schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel

from app.schemas.hotel_schema import PaginatedResponse


class GuestCreate(BaseModel):
    """Guest creation schema."""

    name: str
    phone_number: str
    email: str | None = None
    password: str | None = None


class GuestUpdate(BaseModel):
    """Guest update schema (no password in this phase)."""

    name: str | None = None
    phone_number: str | None = None
    email: str | None = None


class GuestRead(BaseModel):
    """Guest response schema (excludes password)."""

    id: int
    name: str
    phone_number: str
    email: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


GuestIndexResponse = PaginatedResponse[GuestRead]
