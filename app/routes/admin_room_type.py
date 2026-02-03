"""Admin room type routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.dependencies.auth import get_current_guest
from app.models.guest import Guest
from app.schemas.room_type_schema import (
    RoomTypeCreate,
    RoomTypeIndexResponse,
    RoomTypeRead,
    RoomTypeUpdate,
)
from app.services.room_type_service import RoomTypeService
from database import get_session

router = APIRouter(prefix="/admin/room-types", tags=["admin-room-types"])


@router.get("/", response_model=RoomTypeIndexResponse)
def list_room_types(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=20),
    session: Session = Depends(get_session),
    current_guest: Guest = Depends(get_current_guest),
) -> RoomTypeIndexResponse:
    """List all room types with pagination."""
    service = RoomTypeService(session)
    return service.list_room_types(page, page_size)


@router.get("/location/{location_id}", response_model=RoomTypeIndexResponse)
def list_room_types_by_location(
    location_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=20),
    session: Session = Depends(get_session),
    current_guest: Guest = Depends(get_current_guest),
) -> RoomTypeIndexResponse:
    """List room types for a specific location with pagination."""
    service = RoomTypeService(session)
    return service.list_by_location(location_id, page, page_size)


@router.post("/", response_model=RoomTypeRead, status_code=status.HTTP_201_CREATED)
def create_room_type(
    data: RoomTypeCreate,
    session: Session = Depends(get_session),
    current_guest: Guest = Depends(get_current_guest),
) -> RoomTypeRead:
    """Create a new room type."""
    service = RoomTypeService(session)
    room_type = service.create(data)
    return RoomTypeRead.model_validate(room_type)


@router.get("/{slug}", response_model=RoomTypeRead)
def get_room_type(
    slug: str,
    session: Session = Depends(get_session),
    current_guest: Guest = Depends(get_current_guest),
) -> RoomTypeRead:
    """Get a room type by slug."""
    service = RoomTypeService(session)
    room_type = service.get_by_slug(slug)
    return RoomTypeRead.model_validate(room_type)


@router.put("/{slug}", response_model=RoomTypeRead)
def update_room_type(
    slug: str,
    data: RoomTypeUpdate,
    session: Session = Depends(get_session),
    current_guest: Guest = Depends(get_current_guest),
) -> RoomTypeRead:
    """Update a room type by slug."""
    service = RoomTypeService(session)
    room_type = service.update(slug, data)
    return RoomTypeRead.model_validate(room_type)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room_type(
    slug: str,
    session: Session = Depends(get_session),
    current_guest: Guest = Depends(get_current_guest),
) -> None:
    """Soft delete a room type by slug."""
    service = RoomTypeService(session)
    service.delete(slug)
