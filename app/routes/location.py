"""Location routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.schemas.location_schema import (
    LocationCreate,
    LocationIndexResponse,
    LocationRead,
    LocationUpdate,
)
from app.services.location_service import LocationService
from database import get_session

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/", response_model=LocationIndexResponse)
def list_locations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=20),
    session: Session = Depends(get_session),
) -> LocationIndexResponse:
    """List all locations with pagination."""
    service = LocationService(session)
    return service.list_locations(page, page_size)


@router.get("/hotel/{hotel_id}", response_model=LocationIndexResponse)
def list_locations_by_hotel(
    hotel_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=20),
    session: Session = Depends(get_session),
) -> LocationIndexResponse:
    """List locations for a specific hotel with pagination."""
    service = LocationService(session)
    return service.list_by_hotel(hotel_id, page, page_size)


@router.post("/", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
def create_location(
    data: LocationCreate,
    session: Session = Depends(get_session),
) -> LocationRead:
    """Create a new location."""
    service = LocationService(session)
    location = service.create(data)
    return LocationRead.model_validate(location)


@router.get("/{slug}", response_model=LocationRead)
def get_location(
    slug: str,
    session: Session = Depends(get_session),
) -> LocationRead:
    """Get a location by slug."""
    service = LocationService(session)
    location = service.get_by_slug(slug)
    return LocationRead.model_validate(location)


@router.put("/{slug}", response_model=LocationRead)
def update_location(
    slug: str,
    data: LocationUpdate,
    session: Session = Depends(get_session),
) -> LocationRead:
    """Update a location by slug."""
    service = LocationService(session)
    location = service.update(slug, data)
    return LocationRead.model_validate(location)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    slug: str,
    session: Session = Depends(get_session),
) -> None:
    """Soft delete a location by slug."""
    service = LocationService(session)
    service.delete(slug)
