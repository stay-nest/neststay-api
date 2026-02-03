"""RoomType service for business logic."""

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.room_type import RoomType
from app.repositories.location_repo import LocationRepository
from app.repositories.room_type_repo import RoomTypeRepository
from app.schemas.room_type_schema import (
    RoomTypeCreate,
    RoomTypeIndexResponse,
    RoomTypeRead,
    RoomTypeUpdate,
)
from app.utils.slug import generate_unique_slug


class RoomTypeService:
    """Service for RoomType business logic."""

    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session
        self.room_type_repo = RoomTypeRepository(session)
        self.location_repo = LocationRepository(session)

    def create(self, data: RoomTypeCreate) -> RoomType:
        """
        Create a new room type with auto-generated unique slug.
        Validates location exists and derives hotel_id from location.

        Args:
            data: RoomType creation data

        Returns:
            Created room type instance

        Raises:
            HTTPException: 404 if location_id doesn't exist
        """
        # Validate location exists
        location = self.location_repo.get_by_id(data.location_id)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location with id '{data.location_id}' not found",
            )

        # Generate unique slug
        slug = generate_unique_slug(
            name=data.name,
            check_exists=self.room_type_repo.slug_exists,
        )

        # Create room type instance (hotel_id derived from location)
        room_type = RoomType(
            location_id=data.location_id,
            hotel_id=location.hotel_id,
            name=data.name,
            slug=slug,
            description=data.description,
            base_price=data.base_price,
            total_inventory=data.total_inventory,
            max_occupancy=data.max_occupancy,
            default_min_stay=data.default_min_stay,
            max_advance_days=data.max_advance_days,
            is_active=True,
        )

        self.room_type_repo.create(room_type)
        self.session.commit()
        self.session.refresh(room_type)

        return room_type

    def list_room_types(self, page: int, page_size: int) -> RoomTypeIndexResponse:
        """List room types with pagination."""
        offset = (page - 1) * page_size
        room_types = self.room_type_repo.get_paginated(offset, page_size)
        total = self.room_type_repo.count()
        items = [RoomTypeRead.model_validate(rt) for rt in room_types]
        return RoomTypeIndexResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def list_by_location(
        self, location_id: int, page: int, page_size: int
    ) -> RoomTypeIndexResponse:
        """
        List room types for a specific location with pagination.

        Args:
            location_id: The location ID to filter by
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Paginated list of room types for the location

        Raises:
            HTTPException: 404 if location doesn't exist
        """
        location = self.location_repo.get_by_id(location_id)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location with id '{location_id}' not found",
            )

        offset = (page - 1) * page_size
        room_types = self.room_type_repo.get_by_location(location_id, offset, page_size)
        total = self.room_type_repo.count_by_location(location_id)
        items = [RoomTypeRead.model_validate(rt) for rt in room_types]
        return RoomTypeIndexResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_by_slug(self, slug: str) -> RoomType:
        """
        Get room type by slug.

        Args:
            slug: The slug to look up

        Returns:
            RoomType instance

        Raises:
            HTTPException: 404 if room type not found or soft-deleted
        """
        room_type = self.room_type_repo.get_by_slug(slug)
        if not room_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Room type with slug '{slug}' not found",
            )
        return room_type

    def update(self, slug: str, data: RoomTypeUpdate) -> RoomType:
        """
        Update a room type by slug.

        Args:
            slug: The slug of the room type to update
            data: RoomType update data

        Returns:
            Updated room type instance

        Raises:
            HTTPException: 404 if room type not found or soft-deleted
        """
        room_type = self.get_by_slug(slug)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(room_type, field, value)

        self.room_type_repo.update(room_type)
        self.session.commit()
        self.session.refresh(room_type)

        return room_type

    def delete(self, slug: str) -> None:
        """
        Soft delete a room type by slug.

        Args:
            slug: The slug of the room type to delete

        Raises:
            HTTPException: 404 if room type not found or soft-deleted
        """
        room_type = self.get_by_slug(slug)
        self.room_type_repo.soft_delete(room_type)
        self.session.commit()
