"""Location service for business logic."""

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.location import Location
from app.models.location_image import LocationImage
from app.repositories.hotel_repo import HotelRepository
from app.repositories.location_repo import LocationRepository
from app.schemas.location_image_schema import LocationImageReadEmbedded
from app.schemas.location_schema import (
    LocationCreate,
    LocationDetailRead,
    LocationIndexResponse,
    LocationRead,
    LocationUpdate,
)
from app.services.storage.base import StorageService
from app.utils.slug import generate_unique_slug


class LocationService:
    """Service for Location business logic."""

    def __init__(self, session: Session, storage: StorageService):
        """Initialize service with database session and storage (for image URLs)."""
        self.session = session
        self.storage = storage
        self.location_repo = LocationRepository(session)
        self.hotel_repo = HotelRepository(session)

    def _image_to_embedded(self, img: LocationImage) -> LocationImageReadEmbedded:
        """Build LocationImageReadEmbedded (no id/location_id) with url from storage."""
        return LocationImageReadEmbedded(
            filename=img.filename,
            file_path=img.file_path,
            url=self.storage.get_url(img.file_path),
            alt_text=img.alt_text,
            is_featured=img.is_featured,
            sort_order=img.sort_order,
            created_at=img.created_at,
        )

    def _location_to_read(self, location: Location) -> LocationRead:
        """Build LocationRead from model including featured_image with URL."""
        featured = None
        if getattr(location, "featured_image", None):
            featured = self._image_to_embedded(location.featured_image)
        return LocationRead(
            slug=location.slug,
            hotel_id=location.hotel_id,
            name=location.name,
            description=location.description,
            address=location.address,
            latitude=location.latitude,
            longitude=location.longitude,
            city=location.city,
            state=location.state,
            country=location.country,
            is_active=location.is_active,
            featured_image=featured,
        )

    def create(self, data: LocationCreate) -> LocationRead:
        """
        Create a new location with auto-generated unique slug.

        Args:
            data: Location creation data

        Returns:
            LocationRead (with featured_image when set)

        Raises:
            HTTPException: 404 if hotel_id doesn't exist
        """
        # Validate hotel exists
        hotel = self.hotel_repo.get_by_id(data.hotel_id)
        if not hotel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hotel with id '{data.hotel_id}' not found",
            )

        # Generate unique slug
        slug = generate_unique_slug(
            name=data.name,
            check_exists=self.location_repo.slug_exists,
        )

        # Create location instance
        location = Location(
            hotel_id=data.hotel_id,
            name=data.name,
            slug=slug,
            description=data.description,
            address=data.address,
            latitude=data.latitude,
            longitude=data.longitude,
            city=data.city,
            state=data.state,
            country=data.country,
            contact_phone=data.contact_phone,
            contact_email=data.contact_email,
            is_active=True,
        )

        # Create location via repository
        self.location_repo.create(location)

        # Increment hotel's location count
        self.hotel_repo.increment_location_count(data.hotel_id)

        # Commit transaction atomically
        self.session.commit()
        self.session.refresh(location)

        return self._location_to_read(location)

    def list_locations(self, page: int, page_size: int) -> LocationIndexResponse:
        """List locations with pagination."""
        # Calculate offset
        offset = (page - 1) * page_size

        # Get paginated locations and total count
        locations = self.location_repo.get_paginated(offset, page_size)
        total = self.location_repo.count()

        # Convert to response schema (featured_image loaded via selectin)
        items = [self._location_to_read(location) for location in locations]

        return LocationIndexResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def list_by_hotel(
        self, hotel_id: int, page: int, page_size: int
    ) -> LocationIndexResponse:
        """
        List locations for a specific hotel with pagination.

        Args:
            hotel_id: The hotel ID to filter by
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Paginated list of locations for the hotel

        Raises:
            HTTPException: 404 if hotel doesn't exist
        """
        # Validate hotel exists
        hotel = self.hotel_repo.get_by_id(hotel_id)
        if not hotel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hotel with id '{hotel_id}' not found",
            )

        # Calculate offset
        offset = (page - 1) * page_size

        # Get paginated locations and total count for this hotel
        locations = self.location_repo.get_by_hotel(hotel_id, offset, page_size)
        total = self.location_repo.count_by_hotel(hotel_id)

        # Convert to response schema (featured_image loaded via selectin)
        items = [self._location_to_read(location) for location in locations]

        return LocationIndexResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_by_slug(self, slug: str) -> Location:
        """
        Get location by slug.

        Args:
            slug: The slug to look up

        Returns:
            Location instance

        Raises:
            HTTPException: 404 if location not found or soft-deleted
        """
        location = self.location_repo.get_by_slug(slug)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location with slug '{slug}' not found",
            )
        return location

    def get_detail_by_slug(self, slug: str) -> LocationDetailRead:
        """
        Get location detail by slug with all images.

        Args:
            slug: The slug to look up

        Returns:
            LocationDetailRead with featured_image and images (with URLs)

        Raises:
            HTTPException: 404 if location not found or soft-deleted
        """
        location = self.location_repo.get_by_slug(slug)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location with slug '{slug}' not found",
            )
        base = self._location_to_read(location)
        images = [self._image_to_embedded(img) for img in location.images]
        return LocationDetailRead(
            **base.model_dump(),
            images=images,
        )

    def update(self, slug: str, data: LocationUpdate) -> LocationRead:
        """
        Update a location by slug.

        Args:
            slug: The slug of the location to update
            data: Location update data

        Returns:
            LocationRead (with featured_image when set)

        Raises:
            HTTPException: 404 if location not found or soft-deleted
        """
        # Get location (raises 404 if not found or soft-deleted)
        location = self.get_by_slug(slug)

        # Update fields from data (only provided fields)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(location, field, value)

        # Update via repository
        self.location_repo.update(location)

        # Commit transaction
        self.session.commit()
        self.session.refresh(location)

        return self._location_to_read(location)

    def delete(self, slug: str) -> None:
        """
        Soft delete a location by slug.

        Args:
            slug: The slug of the location to delete

        Raises:
            HTTPException: 404 if location not found or soft-deleted
        """
        # Get location (raises 404 if not found or soft-deleted)
        location = self.get_by_slug(slug)

        # Soft delete via repository
        self.location_repo.soft_delete(location)

        # Decrement hotel's location count
        self.hotel_repo.decrement_location_count(location.hotel_id)

        # Commit transaction atomically
        self.session.commit()
