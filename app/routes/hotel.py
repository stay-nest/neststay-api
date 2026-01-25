"""Hotel routes."""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from database import get_session
from app.services.hotel import HotelService
from app.schemas.hotel import HotelIndexResponse

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
