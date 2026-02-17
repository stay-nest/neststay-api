"""Booking model and status enum."""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Column, String
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.guest import Guest
    from app.models.hotel import Hotel
    from app.models.location import Location
    from app.models.room_type import RoomType


class BookingStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Booking(SQLModel, table=True):
    """Booking entity model."""

    __tablename__ = "bookings"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(index=True, unique=True)

    guest_id: int = Field(foreign_key="guests.id", index=True)
    room_type_id: int = Field(foreign_key="room_types.id", index=True)
    location_id: int = Field(foreign_key="locations.id", index=True)
    hotel_id: int = Field(foreign_key="hotels.id", index=True)

    check_in: date
    check_out: date

    num_rooms: int = Field(default=1)
    num_guests: int = Field(default=1)

    night_count: int

    price_per_night: Decimal = Field(max_digits=10, decimal_places=2)
    total_price: Decimal = Field(max_digits=12, decimal_places=2)

    status: BookingStatus = Field(
        default=BookingStatus.PENDING,
        sa_column=Column(String(length=50), nullable=False),
    )

    special_requests: str | None = None
    cancellation_reason: str | None = None
    cancelled_at: datetime | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = Field(default=None)

    # Relationships
    guest: "Guest" = Relationship(back_populates="bookings")
    room_type: "RoomType" = Relationship(back_populates="bookings")
    location: "Location" = Relationship(back_populates="bookings")
    hotel: "Hotel" = Relationship(back_populates="bookings")
