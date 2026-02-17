"""Location model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.location_image import LocationImage

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.hotel import Hotel
    from app.models.room_type import RoomType


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

    # Relationships
    hotel: "Hotel" = Relationship(back_populates="locations")
    images: list["LocationImage"] = Relationship(back_populates="location")
    featured_image: LocationImage | None = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "and_(Location.id == foreign(LocationImage.location_id), "
            "LocationImage.is_featured == True)",
            "uselist": False,
            "viewonly": True,
            "lazy": "selectin",
        }
    )
    room_types: list["RoomType"] = Relationship(back_populates="location")
    bookings: list["Booking"] = Relationship(back_populates="location")
