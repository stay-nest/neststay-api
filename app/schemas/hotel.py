"""Hotel schemas for request/response validation."""
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class HotelCreate(BaseModel):
    """Hotel creation schema."""

    name: str
    description: str
    contact_phone: str
    contact_email: str


class HotelUpdate(BaseModel):
    """Hotel update schema (slug is not editable)."""

    name: str | None = None
    description: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None


class HotelRead(BaseModel):
    """Hotel response schema for index endpoint (excludes sensitive fields and id)."""

    name: str
    slug: str
    description: str | None = None
    is_active: bool
    location_count: int

    class Config:
        """Pydantic config."""

        from_attributes = True


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic pagination wrapper schema."""

    items: list[T]
    total: int
    page: int
    page_size: int


HotelIndexResponse = PaginatedResponse[HotelRead]
