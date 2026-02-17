"""Room date-level inventory model."""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.room_type import RoomType


class RoomDateInventory(SQLModel, table=True):
    """Inventory for a room type on a specific date."""

    __tablename__ = "room_date_inventory"  # type: ignore[assignment]
    __table_args__ = (
        UniqueConstraint(
            "room_type_id",
            "date",
            name="uq_room_date_inventory_room_type_date",
        ),
        Index(
            "ix_room_date_inventory_room_type_date",
            "room_type_id",
            "date",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    room_type_id: int = Field(foreign_key="room_types.id", index=True)
    date: date
    total_rooms: int
    booked_count: int = Field(default=0)

    # Relationships
    room_type: "RoomType" = Relationship(back_populates="inventory_dates")
