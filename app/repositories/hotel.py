"""Hotel repository for single-table database operations."""

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import defer
from sqlmodel import Session, func, select

from app.models.hotel import Hotel


class HotelRepository:
    """Repository for Hotel entity operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def get_paginated(self, offset: int, limit: int) -> list[Hotel]:
        """Get paginated list of active hotels."""
        statement = (
            select(Hotel)
            .where(Hotel.is_active)
            .order_by(desc(Hotel.id))
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def count(self) -> int:
        """Get total count of active hotels."""
        statement = select(func.count(Hotel.id)).where(Hotel.is_active)
        result = self.session.exec(statement).one()
        return result

    def create(self, hotel: Hotel) -> Hotel:
        """
        Create a hotel instance.

        Args:
            hotel: Hotel instance to create

        Returns:
            Created hotel instance (not yet committed)
        """
        self.session.add(hotel)
        return hotel

    def slug_exists(self, slug: str) -> bool:
        """
        Check if a slug already exists in the database.

        Args:
            slug: The slug to check

        Returns:
            True if slug exists, False otherwise
        """
        statement = select(Hotel).where(Hotel.slug == slug)
        result = self.session.exec(statement).first()
        return result is not None

    def get_by_slug(self, slug: str) -> Hotel | None:
        """
        Get hotel by slug, excluding soft-deleted hotels.
        Excludes contact_email and contact_phone from the query.

        Args:
            slug: The slug to look up

        Returns:
            Hotel instance if found and active, None otherwise
        """
        statement = (
            select(Hotel)
            .options(
                defer(Hotel.contact_email),
                defer(Hotel.contact_phone),
            )
            .where(Hotel.slug == slug)
            .where(Hotel.is_active)
        )
        return self.session.exec(statement).first()

    def update(self, hotel: Hotel) -> Hotel:
        """
        Update a hotel instance.

        Args:
            hotel: Hotel instance to update

        Returns:
            Updated hotel instance (not yet committed)
        """
        self.session.add(hotel)
        return hotel

    def soft_delete(self, hotel: Hotel) -> Hotel:
        """
        Soft delete a hotel by setting is_active=False and deleted_at timestamp.

        Args:
            hotel: Hotel instance to soft delete

        Returns:
            Updated hotel instance (not yet committed)
        """
        hotel.is_active = False
        hotel.deleted_at = datetime.utcnow()
        self.session.add(hotel)
        return hotel
