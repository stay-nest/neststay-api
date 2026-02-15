"""Location schemas for request/response validation."""

from pydantic import BaseModel

from app.schemas.location_image_schema import LocationImageReadEmbedded


class LocationCreate(BaseModel):
    """Location creation schema."""

    hotel_id: int
    name: str
    description: str | None = None
    address: str
    latitude: float | None = None
    longitude: float | None = None
    city: str
    state: str
    country: str
    contact_phone: str
    contact_email: str | None = None


class LocationUpdate(BaseModel):
    """Location update schema (hotel_id and slug are not editable)."""

    name: str | None = None
    description: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None


class LocationRead(BaseModel):
    """Location response schema (excludes sensitive fields and id)."""

    slug: str
    hotel_id: int
    name: str
    description: str | None = None
    address: str
    latitude: float | None = None
    longitude: float | None = None
    city: str
    state: str
    country: str
    is_active: bool
    featured_image: LocationImageReadEmbedded | None = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class LocationDetailRead(LocationRead):
    """Detail response with all images."""

    images: list[LocationImageReadEmbedded] = []


class LocationIndexResponse(BaseModel):
    """Paginated location list response."""

    items: list[LocationRead]
    total: int
    page: int
    page_size: int
