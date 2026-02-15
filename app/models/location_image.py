"""LocationImage model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.location import Location


class LocationImage(SQLModel, table=True):
    """Location image entity model."""

    __tablename__ = "location_images"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    location_id: int = Field(foreign_key="locations.id", index=True)
    filename: str
    file_path: str
    alt_text: str | None = None
    is_featured: bool = False
    sort_order: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    location: "Location" = Relationship(back_populates="images")
