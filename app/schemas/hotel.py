"""Hotel schemas for request/response validation."""
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


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
