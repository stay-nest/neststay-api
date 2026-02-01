"""Guest schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, model_validator

from app.schemas.hotel_schema import PaginatedResponse


class GuestRegister(BaseModel):
    """Guest registration - phone OR email+password flow."""

    name: str
    phone_number: str | None = None
    email: str | None = None
    password: str | None = None

    @model_validator(mode="after")
    def require_phone_or_email_password(self):
        """Require phone_number OR (email and password). Prefer phone when both."""
        has_phone = bool(self.phone_number and self.phone_number.strip())
        has_email = bool(self.email and self.email.strip())
        has_password = bool(self.password is not None and (self.password or ""))
        if has_phone:
            return self
        if has_email and has_password:
            return self
        if has_email or has_password:
            raise ValueError("Must provide phone_number OR both email and password")
        raise ValueError("Must provide phone_number OR both email and password")


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
