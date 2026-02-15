"""Guest repository for single-table database operations."""

from datetime import datetime

from sqlalchemy import desc
from sqlmodel import Session, func, select

from app.models.guest import Guest


class GuestRepository:
    """Repository for Guest entity operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create(self, guest: Guest) -> Guest:
        """
        Create a guest instance.

        Args:
            guest: Guest instance to create

        Returns:
            Created guest instance (not yet committed)
        """
        self.session.add(guest)
        return guest

    def get_guest_by_phone_number(self, phone_number: str) -> Guest | None:
        """
        Get guest by phone number, excluding inactive guests.

        Args:
            phone_number: The phone number to look up

        Returns:
            Guest instance if found and active, None otherwise
        """
        statement = (
            select(Guest)
            .where(Guest.phone_number == phone_number)
            .where(Guest.is_active)
        )
        return self.session.exec(statement).first()

    def get_guest_by_email(self, email: str) -> Guest | None:
        """
        Get guest by email, excluding inactive guests.

        Args:
            email: The email to look up

        Returns:
            Guest instance if found and active, None otherwise
        """
        statement = select(Guest).where(Guest.email == email).where(Guest.is_active)
        return self.session.exec(statement).first()

    def get_guest_by_id(self, guest_id: int) -> Guest | None:
        """
        Get guest by ID, excluding inactive guests.

        Args:
            guest_id: The guest ID to look up

        Returns:
            Guest instance if found and active, None otherwise
        """
        statement = select(Guest).where(Guest.id == guest_id).where(Guest.is_active)
        return self.session.exec(statement).first()

    def get_paginated(self, offset: int, limit: int) -> list[Guest]:
        """Get paginated list of active guests."""
        statement = (
            select(Guest)
            .where(Guest.is_active)
            .order_by(desc(Guest.id))  # type: ignore[arg-type]
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def count(self) -> int:
        """Get total count of active guests."""
        statement = select(func.count(Guest.id)).where(Guest.is_active)  # type: ignore[arg-type]
        result = self.session.exec(statement).one()
        return result

    def update_guest(self, guest: Guest) -> Guest:
        """
        Update a guest instance.

        Args:
            guest: Guest instance to update

        Returns:
            Updated guest instance (not yet committed)
        """
        self.session.add(guest)
        return guest

    def delete_guest(self, guest: Guest) -> Guest:
        """
        Soft delete a guest by setting is_active=False and deleted_at timestamp.

        Args:
            guest: Guest instance to soft delete

        Returns:
            Updated guest instance (not yet committed)
        """
        guest.is_active = False
        guest.deleted_at = datetime.utcnow()
        self.session.add(guest)
        return guest
