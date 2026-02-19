"""Booking repository for single-table database operations."""

from datetime import datetime

from sqlalchemy import desc
from sqlmodel import Session, func, select

from app.models.booking import Booking


class BookingRepository:
    """Repository for Booking entity operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create(self, booking: Booking) -> Booking:
        """
        Create a booking instance.

        Args:
            booking: Booking instance to create

        Returns:
            Created booking instance (not yet committed)
        """
        self.session.add(booking)
        return booking

    def get_by_slug(self, slug: str) -> Booking | None:
        """
        Get booking by slug, excluding soft-deleted bookings.

        Args:
            slug: The slug to look up

        Returns:
            Booking instance if found, None otherwise
        """
        statement = (
            select(Booking)
            .where(Booking.slug == slug)
            .where(Booking.deleted_at.is_(None))
        )
        return self.session.exec(statement).first()

    def get_by_guest(self, guest_id: int, offset: int, limit: int) -> list[Booking]:
        """
        Get paginated list of bookings for a guest, excluding soft-deleted.

        Args:
            guest_id: The guest ID to filter by
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of bookings ordered by check_in descending
        """
        statement = (
            select(Booking)
            .where(Booking.guest_id == guest_id)
            .where(Booking.deleted_at.is_(None))
            .order_by(desc(Booking.check_in))
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def count_by_guest(self, guest_id: int) -> int:
        """
        Get total count of non-deleted bookings for a guest.

        Args:
            guest_id: The guest ID to filter by

        Returns:
            Count of bookings
        """
        statement = (
            select(func.count(Booking.id))
            .where(Booking.guest_id == guest_id)
            .where(Booking.deleted_at.is_(None))
        )
        result = self.session.exec(statement).one()
        return result

    def update(self, booking: Booking) -> Booking:
        """
        Update a booking instance.

        Args:
            booking: Booking instance to update

        Returns:
            Updated booking instance (not yet committed)
        """
        self.session.add(booking)
        return booking

    def soft_delete(self, booking: Booking) -> Booking:
        """
        Soft delete a booking by setting deleted_at timestamp.

        Args:
            booking: Booking instance to soft delete

        Returns:
            Updated booking instance (not yet committed)
        """
        booking.deleted_at = datetime.utcnow()
        self.session.add(booking)
        return booking

    def slug_exists(self, slug: str) -> bool:
        """
        Check if a slug already exists among non-deleted bookings.

        Args:
            slug: The slug to check

        Returns:
            True if slug exists, False otherwise
        """
        statement = (
            select(Booking)
            .where(Booking.slug == slug)
            .where(Booking.deleted_at.is_(None))
        )
        result = self.session.exec(statement).first()
        return result is not None
