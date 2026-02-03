"""RoomType schemas for request/response validation."""

from decimal import Decimal

from pydantic import BaseModel


class RoomTypeCreate(BaseModel):
    """RoomType creation. location_id required, hotel_id derived from location."""

    location_id: int
    name: str
    description: str | None = None
    base_price: Decimal = Decimal("0.00")
    total_inventory: int = 0
    max_occupancy: int = 1
    default_min_stay: int = 1
    max_advance_days: int = 365


class RoomTypeUpdate(BaseModel):
    """RoomType update schema (all fields optional)."""

    name: str | None = None
    description: str | None = None
    base_price: Decimal | None = None
    total_inventory: int | None = None
    max_occupancy: int | None = None
    default_min_stay: int | None = None
    max_advance_days: int | None = None


class RoomTypeRead(BaseModel):
    """RoomType response schema."""

    slug: str
    location_id: int
    hotel_id: int
    name: str
    description: str | None = None
    base_price: Decimal
    total_inventory: int
    max_occupancy: int
    default_min_stay: int
    max_advance_days: int
    is_active: bool

    class Config:
        """Pydantic config."""

        from_attributes = True


class RoomTypeIndexResponse(BaseModel):
    """Paginated room type list response."""

    items: list[RoomTypeRead]
    total: int
    page: int
    page_size: int
