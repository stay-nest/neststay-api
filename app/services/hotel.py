"""Hotel service for business logic."""
from sqlmodel import Session
from app.repositories.hotel import HotelRepository
from app.schemas.hotel import HotelIndexResponse, HotelRead


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
