"""RoomType model."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.hotel import Hotel
    from app.models.location import Location
    from app.models.room_date_inventory import RoomDateInventory


class RoomType(SQLModel, table=True):
    """RoomType entity model - room categories per location."""

    __tablename__ = "room_types"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    location_id: int = Field(foreign_key="locations.id", index=True)
    hotel_id: int = Field(foreign_key="hotels.id", index=True)
    name: str
    slug: str = Field(unique=True)
    description: str | None = None
    base_price: Decimal = Field(
        default=Decimal("0.00"), max_digits=10, decimal_places=2
    )
    total_inventory: int = Field(default=0)
    max_occupancy: int = Field(default=1)
    default_min_stay: int = Field(default=1)
    max_advance_days: int = Field(default=365)
    is_active: bool = Field(default=True)
    deleted_at: datetime | None = Field(default=None)

    # Relationships
    location: "Location" = Relationship(back_populates="room_types")
    hotel: "Hotel" = Relationship(back_populates="room_types")
    bookings: list["Booking"] = Relationship(back_populates="room_type")
    inventory_dates: list["RoomDateInventory"] = Relationship(
        back_populates="room_type"
    )
