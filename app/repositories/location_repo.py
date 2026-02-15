"""Location repository for single-table database operations."""

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import defer, selectinload
from sqlmodel import Session, func, select

from app.models.location import Location


class LocationRepository:
    """Repository for Location entity operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create(self, location: Location) -> Location:
        """
        Create a location instance.

        Args:
            location: Location instance to create

        Returns:
            Created location instance (not yet committed)
        """
        self.session.add(location)
        return location

    def get_by_id(self, location_id: int) -> Location | None:
        """
        Get location by ID, excluding soft-deleted locations.

        Args:
            location_id: The location ID to look up

        Returns:
            Location instance if found and active, None otherwise
        """
        statement = (
            select(Location).where(Location.id == location_id).where(Location.is_active)
        )
        return self.session.exec(statement).first()

    def get_by_slug(self, slug: str) -> Location | None:
        """
        Get location by slug, excluding soft-deleted locations.
        Excludes contact_email and contact_phone from the query.

        Args:
            slug: The slug to look up

        Returns:
            Location instance if found and active, None otherwise
        """
        statement = (
            select(Location)
            .options(
                defer(Location.contact_email),
                defer(Location.contact_phone),
                selectinload(Location.images),
            )
            .where(Location.slug == slug)
            .where(Location.is_active)
        )
        return self.session.exec(statement).first()

    def get_paginated(self, offset: int, limit: int) -> list[Location]:
        """Get paginated list of active locations."""
        statement = (
            select(Location)
            .where(Location.is_active)
            .order_by(desc(Location.id))  # type: ignore[arg-type]
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def get_by_hotel(self, hotel_id: int, offset: int, limit: int) -> list[Location]:
        """
        Get paginated list of active locations for a specific hotel.

        Args:
            hotel_id: The hotel ID to filter by
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active locations for the hotel
        """
        statement = (
            select(Location)
            .where(Location.hotel_id == hotel_id)
            .where(Location.is_active)
            .order_by(desc(Location.id))  # type: ignore[arg-type]
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def count(self) -> int:
        """Get total count of active locations."""
        statement = select(func.count(Location.id)).where(Location.is_active)  # type: ignore[arg-type]
        result = self.session.exec(statement).one()
        return result

    def count_by_hotel(self, hotel_id: int) -> int:
        """
        Get count of active locations for a specific hotel.

        Args:
            hotel_id: The hotel ID to filter by

        Returns:
            Count of active locations for the hotel
        """
        statement = (
            select(func.count(Location.id))  # type: ignore[arg-type]
            .where(Location.hotel_id == hotel_id)
            .where(Location.is_active)
        )
        result = self.session.exec(statement).one()
        return result

    def slug_exists(self, slug: str) -> bool:
        """
        Check if a slug already exists in the database.

        Args:
            slug: The slug to check

        Returns:
            True if slug exists, False otherwise
        """
        statement = select(Location).where(Location.slug == slug)
        result = self.session.exec(statement).first()
        return result is not None

    def update(self, location: Location) -> Location:
        """
        Update a location instance.

        Args:
            location: Location instance to update

        Returns:
            Updated location instance (not yet committed)
        """
        self.session.add(location)
        return location

    def soft_delete(self, location: Location) -> Location:
        """
        Soft delete a location by setting is_active=False and deleted_at timestamp.

        Args:
            location: Location instance to soft delete

        Returns:
            Updated location instance (not yet committed)
        """
        location.is_active = False
        location.deleted_at = datetime.utcnow()
        self.session.add(location)
        return location
