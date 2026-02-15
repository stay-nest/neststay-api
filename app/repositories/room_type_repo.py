"""RoomType repository for single-table database operations."""

from datetime import UTC, datetime

from sqlalchemy import desc
from sqlmodel import Session, func, select

from app.models.room_type import RoomType


class RoomTypeRepository:
    """Repository for RoomType entity operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create(self, room_type: RoomType) -> RoomType:
        """
        Create a room type instance.

        Args:
            room_type: RoomType instance to create

        Returns:
            Created room type instance (not yet committed)
        """
        self.session.add(room_type)
        return room_type

    def get_by_slug(self, slug: str) -> RoomType | None:
        """
        Get room type by slug, excluding soft-deleted room types.

        Args:
            slug: The slug to look up

        Returns:
            RoomType instance if found and active, None otherwise
        """
        statement = (
            select(RoomType).where(RoomType.slug == slug).where(RoomType.is_active)
        )
        return self.session.exec(statement).first()

    def get_paginated(self, offset: int, limit: int) -> list[RoomType]:
        """Get paginated list of active room types."""
        statement = (
            select(RoomType)
            .where(RoomType.is_active)
            .order_by(desc(RoomType.id))  # type: ignore[arg-type]
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def get_by_location(
        self, location_id: int, offset: int, limit: int
    ) -> list[RoomType]:
        """
        Get paginated list of active room types for a specific location.

        Args:
            location_id: The location ID to filter by
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active room types for the location
        """
        statement = (
            select(RoomType)
            .where(RoomType.location_id == location_id)
            .where(RoomType.is_active)
            .order_by(desc(RoomType.id))  # type: ignore[arg-type]
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def get_by_hotel(self, hotel_id: int, offset: int, limit: int) -> list[RoomType]:
        """
        Get paginated list of active room types for a specific hotel.

        Args:
            hotel_id: The hotel ID to filter by
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active room types for the hotel
        """
        statement = (
            select(RoomType)
            .where(RoomType.hotel_id == hotel_id)
            .where(RoomType.is_active)
            .order_by(desc(RoomType.id))  # type: ignore[arg-type]
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def count(self) -> int:
        """Get total count of active room types."""
        statement = select(func.count(RoomType.id)).where(RoomType.is_active)  # type: ignore[arg-type]
        result = self.session.exec(statement).one()
        return result

    def count_by_location(self, location_id: int) -> int:
        """
        Get count of active room types for a specific location.

        Args:
            location_id: The location ID to filter by

        Returns:
            Count of active room types for the location
        """
        statement = (
            select(func.count(RoomType.id))  # type: ignore[arg-type]
            .where(RoomType.location_id == location_id)
            .where(RoomType.is_active)
        )
        result = self.session.exec(statement).one()
        return result

    def count_by_hotel(self, hotel_id: int) -> int:
        """
        Get count of active room types for a specific hotel.

        Args:
            hotel_id: The hotel ID to filter by

        Returns:
            Count of active room types for the hotel
        """
        statement = (
            select(func.count(RoomType.id))  # type: ignore[arg-type]
            .where(RoomType.hotel_id == hotel_id)
            .where(RoomType.is_active)
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
        statement = select(RoomType).where(RoomType.slug == slug)
        result = self.session.exec(statement).first()
        return result is not None

    def update(self, room_type: RoomType) -> RoomType:
        """
        Update a room type instance.

        Args:
            room_type: RoomType instance to update

        Returns:
            Updated room type instance (not yet committed)
        """
        self.session.add(room_type)
        return room_type

    def soft_delete(self, room_type: RoomType) -> RoomType:
        """
        Soft delete a room type by setting is_active=False and deleted_at timestamp.

        Args:
            room_type: RoomType instance to soft delete

        Returns:
            Updated room type instance (not yet committed)
        """
        room_type.is_active = False
        room_type.deleted_at = datetime.now(UTC)
        self.session.add(room_type)
        return room_type
