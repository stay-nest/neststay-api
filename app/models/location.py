"""Location model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.hotel import Hotel


class Location(SQLModel, table=True):
    """Location entity model."""

    __tablename__ = "locations"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    hotel_id: int = Field(foreign_key="hotels.id", index=True)
    name: str
    description: str | None = None
    slug: str = Field(unique=True)
    address: str
    latitude: float | None = None
    longitude: float | None = None
    city: str
    state: str
    country: str
    contact_phone: str
    contact_email: str | None = None
    is_active: bool = Field(default=True)
    deleted_at: datetime | None = Field(default=None)

    # Relationship to Hotel
    hotel: "Hotel" = Relationship(back_populates="locations")
