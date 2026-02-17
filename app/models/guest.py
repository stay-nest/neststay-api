"""Guest model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.booking import Booking


class Guest(SQLModel, table=True):
    """Guest entity model."""

    __tablename__ = "guests"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str | None = None
    phone_number: str = Field(unique=True)
    password: str | None = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = Field(default=None)

    # Relationships
    bookings: list["Booking"] = Relationship(back_populates="guest")
