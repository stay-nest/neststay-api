"""Hotel routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.schemas.hotel import HotelCreate, HotelIndexResponse, HotelRead, HotelUpdate
from app.services.hotel import HotelService
from database import get_session

router = APIRouter(prefix="/hotels", tags=["hotels"])


@router.get("/", response_model=HotelIndexResponse)
def list_hotels(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=20),
    session: Session = Depends(get_session),
) -> HotelIndexResponse:
    """List hotels with pagination."""
    service = HotelService(session)
    return service.list_hotels(page, page_size)


@router.post("/", response_model=HotelRead, status_code=201)
def create_hotel(
    data: HotelCreate,
    session: Session = Depends(get_session),
) -> HotelRead:
    """Create a new hotel."""
    service = HotelService(session)
    hotel = service.create(data)
    return HotelRead.model_validate(hotel)


@router.get("/{slug}", response_model=HotelRead)
def get_hotel(
    slug: str,
    session: Session = Depends(get_session),
) -> HotelRead:
    """Get a hotel by slug."""
    service = HotelService(session)
    hotel = service.get_by_slug(slug)
    return HotelRead.model_validate(hotel)


@router.put("/{slug}", response_model=HotelRead)
def update_hotel(
    slug: str,
    data: HotelUpdate,
    session: Session = Depends(get_session),
) -> HotelRead:
    """Update a hotel by slug."""
    service = HotelService(session)
    hotel = service.update(slug, data)
    return HotelRead.model_validate(hotel)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hotel(
    slug: str,
    session: Session = Depends(get_session),
) -> None:
    """Soft delete a hotel by slug."""
    service = HotelService(session)
    service.delete(slug)
