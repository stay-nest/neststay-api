"""Public guest routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.schemas.guest_schema import GuestRead, GuestRegister, GuestUpdate
from app.services.guest_service import GuestService
from database import get_session

router = APIRouter(prefix="/guest", tags=["guest"])


@router.post("/register", response_model=GuestRead, status_code=status.HTTP_201_CREATED)
def register_guest(
    data: GuestRegister,
    session: Session = Depends(get_session),
) -> GuestRead:
    """Register a new guest (phone or email+password flow)."""
    service = GuestService(session)
    if data.phone_number and data.phone_number.strip():
        guest = service.register_guest_by_phone_number(
            data.name, data.phone_number, email=data.email
        )
    elif data.email and data.password is not None:
        guest = service.register_guest_by_email(data.name, data.email, data.password)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide phone_number OR both email and password",
        )
    return GuestRead.model_validate(guest)


@router.get("/by-phone/{phone_number}", response_model=GuestRead)
def get_guest_by_phone(
    phone_number: str,
    session: Session = Depends(get_session),
) -> GuestRead:
    """Get guest by phone number."""
    service = GuestService(session)
    guest = service.get_guest_by_phone_number(phone_number)
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guest with phone number '{phone_number}' not found",
        )
    return GuestRead.model_validate(guest)


@router.get("/by-email/{email}", response_model=GuestRead)
def get_guest_by_email(
    email: str,
    session: Session = Depends(get_session),
) -> GuestRead:
    """Get guest by email."""
    service = GuestService(session)
    guest = service.get_guest_by_email(email)
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guest with email '{email}' not found",
        )
    return GuestRead.model_validate(guest)


@router.get("/{guest_id}", response_model=GuestRead)
def get_guest(
    guest_id: int,
    session: Session = Depends(get_session),
) -> GuestRead:
    """Get guest by ID."""
    service = GuestService(session)
    guest = service.get_guest_by_id(guest_id)
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guest with id '{guest_id}' not found",
        )
    return GuestRead.model_validate(guest)


@router.put("/{guest_id}", response_model=GuestRead)
def update_guest(
    guest_id: int,
    data: GuestUpdate,
    session: Session = Depends(get_session),
) -> GuestRead:
    """Update a guest by ID."""
    service = GuestService(session)
    guest = service.update_guest(guest_id, data)
    return GuestRead.model_validate(guest)


@router.delete("/{guest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_guest(
    guest_id: int,
    session: Session = Depends(get_session),
) -> None:
    """Soft delete a guest by ID."""
    service = GuestService(session)
    service.delete_guest(guest_id)
