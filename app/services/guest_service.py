"""Guest service for business logic."""

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.guest import Guest
from app.repositories.guest_repo import GuestRepository
from app.schemas.guest_schema import (
    GuestCreate,
    GuestIndexResponse,
    GuestRead,
    GuestUpdate,
)
from app.utils.password import hash_password


class GuestService:
    """Service for Guest business logic."""

    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session
        self.guest_repo = GuestRepository(session)

    def create_guest(self, data: GuestCreate) -> Guest:
        """
        Create a new guest.

        Args:
            data: Guest creation data

        Returns:
            Created guest instance
        """
        password_hash = hash_password(data.password) if data.password else None
        guest = Guest(
            name=data.name,
            phone_number=data.phone_number,
            email=data.email,
            password=password_hash,
            is_active=True,
        )
        self.guest_repo.create(guest)
        self.session.commit()
        self.session.refresh(guest)
        return guest

    def get_guest_by_phone_number(self, phone_number: str) -> Guest | None:
        """Get guest by phone number. Returns None if not found."""
        return self.guest_repo.get_guest_by_phone_number(phone_number)

    def get_guest_by_email(self, email: str) -> Guest | None:
        """Get guest by email. Returns None if not found."""
        return self.guest_repo.get_guest_by_email(email)

    def get_guest_by_id(self, guest_id: int) -> Guest | None:
        """Get guest by ID. Returns None if not found."""
        return self.guest_repo.get_guest_by_id(guest_id)

    def get_all_guests(self, page: int, page_size: int) -> GuestIndexResponse:
        """List guests with pagination."""
        offset = (page - 1) * page_size
        guests = self.guest_repo.get_paginated(offset, page_size)
        total = self.guest_repo.count()
        items = [GuestRead.model_validate(g) for g in guests]
        return GuestIndexResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def update_guest(self, guest_id: int, data: GuestUpdate) -> Guest:
        """
        Update a guest by ID.

        Args:
            guest_id: The guest ID to update
            data: Guest update data

        Returns:
            Updated guest instance

        Raises:
            HTTPException: 404 if guest not found
        """
        guest = self.guest_repo.get_guest_by_id(guest_id)
        if not guest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Guest with id '{guest_id}' not found",
            )
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(guest, field, value)
        self.guest_repo.update_guest(guest)
        self.session.commit()
        self.session.refresh(guest)
        return guest

    def delete_guest(self, guest_id: int) -> None:
        """
        Hard delete a guest by ID.

        Args:
            guest_id: The guest ID to delete

        Raises:
            HTTPException: 404 if guest not found
        """
        guest = self.guest_repo.get_guest_by_id(guest_id)
        if not guest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Guest with id '{guest_id}' not found",
            )
        self.guest_repo.delete_guest(guest)
        self.session.commit()

    def register_guest_by_phone_number(
        self, name: str, phone_number: str, email: str | None = None
    ) -> Guest:
        """
        Register a guest by phone number (mobile flow; no password).

        Args:
            name: Guest name
            phone_number: Guest phone number (must be unique)
            email: Optional email to store when user provides both phone and email

        Returns:
            Created guest instance

        Raises:
            HTTPException: 409 if phone number already registered
        """
        existing = self.guest_repo.get_guest_by_phone_number(phone_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Guest with this phone number already registered",
            )
        guest = Guest(
            name=name,
            phone_number=phone_number,
            email=email,
            password=None,
            is_active=True,
        )
        self.guest_repo.create(guest)
        self.session.commit()
        self.session.refresh(guest)
        return guest

    def register_guest_by_email(
        self,
        name: str,
        email: str,
        password: str,
    ) -> Guest:
        """
        Register a guest by email (email flow; password required).

        Uses a unique placeholder for phone_number since the model requires it.
        Caller can update phone_number later if collected.

        Args:
            name: Guest name
            email: Guest email (must be unique among active guests)
            password: Plain-text password (will be hashed)

        Returns:
            Created guest instance

        Raises:
            HTTPException: 409 if email already registered
        """
        existing = self.guest_repo.get_guest_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Guest with this email already registered",
            )
        phone_placeholder = f"email-{email}"
        password_hash = hash_password(password)
        guest = Guest(
            name=name,
            phone_number=phone_placeholder,
            email=email,
            password=password_hash,
            is_active=True,
        )
        self.guest_repo.create(guest)
        self.session.commit()
        self.session.refresh(guest)
        return guest
