"""Hotel service for business logic."""
from fastapi import HTTPException, status
from sqlmodel import Session
from app.repositories.hotel import HotelRepository
from app.schemas.hotel import HotelIndexResponse, HotelRead, HotelCreate, HotelUpdate
from app.models.hotel import Hotel
from app.utils.slug import generate_unique_slug


class HotelService:
    """Service for Hotel business logic."""

    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session
        self.hotel_repo = HotelRepository(session)

    def list_hotels(self, page: int, page_size: int) -> HotelIndexResponse:
        """List hotels with pagination."""
        # Calculate offset
        offset = (page - 1) * page_size

        # Get paginated hotels and total count
        hotels = self.hotel_repo.get_paginated(offset, page_size)
        total = self.hotel_repo.count()

        # Convert to response schema
        items = [HotelRead.model_validate(hotel) for hotel in hotels]

        return HotelIndexResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def create(self, data: HotelCreate) -> Hotel:
        """
        Create a new hotel with auto-generated unique slug.

        Args:
            data: Hotel creation data

        Returns:
            Created hotel instance
        """
        # Generate unique slug
        slug = generate_unique_slug(
            name=data.name,
            check_exists=self.hotel_repo.slug_exists,
        )

        # Create hotel instance
        hotel = Hotel(
            name=data.name,
            slug=slug,
            description=data.description,
            contact_phone=data.contact_phone,
            contact_email=data.contact_email,
            is_active=True,
            location_count=0,
        )

        # Create hotel via repository
        self.hotel_repo.create(hotel)

        # Commit transaction
        self.session.commit()
        self.session.refresh(hotel)

        return hotel

    def get_by_slug(self, slug: str) -> Hotel:
        """
        Get hotel by slug.

        Args:
            slug: The slug to look up

        Returns:
            Hotel instance

        Raises:
            HTTPException: 404 if hotel not found or soft-deleted
        """
        hotel = self.hotel_repo.get_by_slug(slug)
        if not hotel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hotel with slug '{slug}' not found",
            )
        return hotel

    def update(self, slug: str, data: HotelUpdate) -> Hotel:
        """
        Update a hotel by slug.

        Args:
            slug: The slug of the hotel to update
            data: Hotel update data

        Returns:
            Updated hotel instance

        Raises:
            HTTPException: 404 if hotel not found or soft-deleted
        """
        # Get hotel (raises 404 if not found or soft-deleted)
        hotel = self.get_by_slug(slug)

        # Update fields from data (only provided fields)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(hotel, field, value)

        # Update via repository
        self.hotel_repo.update(hotel)

        # Commit transaction
        self.session.commit()
        self.session.refresh(hotel)

        return hotel

    def delete(self, slug: str) -> None:
        """
        Soft delete a hotel by slug.

        Args:
            slug: The slug of the hotel to delete

        Raises:
            HTTPException: 404 if hotel not found or soft-deleted
        """
        # Get hotel (raises 404 if not found or soft-deleted)
        hotel = self.get_by_slug(slug)

        # Soft delete via repository
        self.hotel_repo.soft_delete(hotel)

        # Commit transaction
        self.session.commit()
