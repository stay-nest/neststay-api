"""Admin guest routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.schemas.guest_schema import GuestIndexResponse
from app.services.guest_service import GuestService
from database import get_session

router = APIRouter(prefix="/admin/guest", tags=["admin-guest"])


@router.get("/", response_model=GuestIndexResponse)
def list_guests(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=20),
    session: Session = Depends(get_session),
) -> GuestIndexResponse:
    """List all guests with pagination."""
    service = GuestService(session)
    return service.get_all_guests(page, page_size)


@router.delete("/{guest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_guest(
    guest_id: int,
    session: Session = Depends(get_session),
) -> None:
    """Soft delete a guest by ID."""
    service = GuestService(session)
    service.delete_guest(guest_id)
