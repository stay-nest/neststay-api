"""Location routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.schemas.location_schema import (
    LocationCreate,
    LocationDetailRead,
    LocationIndexResponse,
    LocationRead,
    LocationUpdate,
)
from app.services.location_service import LocationService
from app.services.storage import get_storage_service
from config import settings
from database import get_session

router = APIRouter(prefix="/locations", tags=["locations"])


def get_storage():
    """Dependency that returns the configured storage service."""
    return get_storage_service(settings)


@router.get("/", response_model=LocationIndexResponse)
def list_locations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=20),
    session: Session = Depends(get_session),
    storage=Depends(get_storage),
) -> LocationIndexResponse:
    """List all locations with pagination."""
    service = LocationService(session, storage)
    return service.list_locations(page, page_size)


@router.get("/hotel/{hotel_id}", response_model=LocationIndexResponse)
def list_locations_by_hotel(
    hotel_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=20),
    session: Session = Depends(get_session),
    storage=Depends(get_storage),
) -> LocationIndexResponse:
    """List locations for a specific hotel with pagination."""
    service = LocationService(session, storage)
    return service.list_by_hotel(hotel_id, page, page_size)


@router.post("/", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
def create_location(
    data: LocationCreate,
    session: Session = Depends(get_session),
    storage=Depends(get_storage),
) -> LocationRead:
    """Create a new location."""
    service = LocationService(session, storage)
    return service.create(data)


@router.get("/{slug}", response_model=LocationDetailRead)
def get_location(
    slug: str,
    session: Session = Depends(get_session),
    storage=Depends(get_storage),
) -> LocationDetailRead:
    """Get a location by slug with all images."""
    service = LocationService(session, storage)
    return service.get_detail_by_slug(slug)


@router.put("/{slug}", response_model=LocationRead)
def update_location(
    slug: str,
    data: LocationUpdate,
    session: Session = Depends(get_session),
    storage=Depends(get_storage),
) -> LocationRead:
    """Update a location by slug."""
    service = LocationService(session, storage)
    return service.update(slug, data)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    slug: str,
    session: Session = Depends(get_session),
    storage=Depends(get_storage),
) -> None:
    """Soft delete a location by slug."""
    service = LocationService(session, storage)
    service.delete(slug)
