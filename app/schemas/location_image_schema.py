"""Location image schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LocationImageCreate(BaseModel):
    """Location image creation schema (file comes via multipart; alt_text optional)."""

    alt_text: str | None = None


class LocationImageUpdate(BaseModel):
    """Location image update schema."""

    alt_text: str | None = None
    sort_order: int | None = None


class LocationImageRead(BaseModel):
    """Location image response schema with computed url."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    location_id: int
    filename: str
    file_path: str
    url: str
    alt_text: str | None = None
    is_featured: bool
    sort_order: int
    created_at: datetime
