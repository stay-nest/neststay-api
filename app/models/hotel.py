"""Hotel model."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class Hotel(SQLModel, table=True):
    """Hotel entity model."""

    __tablename__ = "hotels"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    name: str
    slug: str = Field(unique=True)
    description: str | None = None
    contact_phone: str
    is_active: bool = Field(default=True)
    contact_email: str | None = None
    location_count: int = Field(default=0)
    deleted_at: datetime | None = Field(default=None)
