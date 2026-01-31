"""Unit tests for GuestService."""

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from app.models.guest import Guest
from app.schemas.guest_schema import GuestCreate, GuestUpdate
from app.services.guest_service import GuestService


class TestGuestServiceCreateGuest:
    """Tests for GuestService.create_guest."""

    def test_create_guest_without_password(self, session: Session) -> None:
        """Should create guest when password is not provided."""
        service = GuestService(session)
        data = GuestCreate(
            name="Jane",
            phone_number="+19999999999",
            email=None,
            password=None,
        )
        guest = service.create_guest(data)
        assert guest.id is not None
        assert guest.name == "Jane"
        assert guest.password is None

    def test_create_guest_with_password_hashes_it(self, session: Session) -> None:
        """Should hash password when provided."""
        service = GuestService(session)
        data = GuestCreate(
            name="Jane",
            phone_number="+19999999999",
            email="jane@test.com",
            password="secret123",
        )
        guest = service.create_guest(data)
        assert guest.password is not None
        assert guest.password != "secret123"
        assert guest.password.startswith("$2")  # bcrypt prefix


class TestGuestServiceGetAllGuests:
    """Tests for GuestService.get_all_guests."""

    def test_get_all_guests_empty(self, session: Session) -> None:
        """Should return empty paginated response when no guests."""
        service = GuestService(session)
        result = service.get_all_guests(page=1, page_size=10)
        assert result.items == []
        assert result.total == 0
        assert result.page == 1
        assert result.page_size == 10

    def test_get_all_guests_paginated(self, session: Session) -> None:
        """Should return paginated list and total."""
        service = GuestService(session)
        for i in range(3):
            service.register_guest_by_phone_number(f"Guest {i}", f"+1999999999{i}")
        result = service.get_all_guests(page=1, page_size=2)
        assert len(result.items) == 2
        assert result.total == 3
        assert result.page == 1
        assert result.page_size == 2


class TestGuestServiceUpdateAndDeleteGuest:
    """Tests for GuestService.update_guest and delete_guest."""

    def test_update_guest_success(self, session: Session) -> None:
        """Should update guest and return updated instance."""
        service = GuestService(session)
        guest = service.register_guest_by_phone_number("Jane", "+19999999999")
        updated = service.update_guest(
            guest.id,
            GuestUpdate(name="Jane Doe"),
        )
        assert updated.name == "Jane Doe"

    def test_update_guest_not_found_raises_404(self, session: Session) -> None:
        """Should raise 404 when guest id does not exist."""
        service = GuestService(session)
        with pytest.raises(HTTPException) as exc_info:
            service.update_guest(99999, GuestUpdate(name="X"))
        assert exc_info.value.status_code == 404

    def test_delete_guest_success(self, session: Session) -> None:
        """Should delete guest by id."""
        service = GuestService(session)
        guest = service.register_guest_by_phone_number("Jane", "+19999999999")
        service.delete_guest(guest.id)
        assert service.get_guest_by_id(guest.id) is None

    def test_delete_guest_not_found_raises_404(self, session: Session) -> None:
        """Should raise 404 when guest id does not exist."""
        service = GuestService(session)
        with pytest.raises(HTTPException) as exc_info:
            service.delete_guest(99999)
        assert exc_info.value.status_code == 404


class TestGuestServiceRegisterByPhoneNumber:
    """Tests for GuestService.register_guest_by_phone_number."""

    def test_register_creates_guest(self, session: Session) -> None:
        """Should create guest with name and phone_number only."""
        service = GuestService(session)
        guest = service.register_guest_by_phone_number("Jane", "+19999999999")
        assert guest.id is not None
        assert guest.name == "Jane"
        assert guest.phone_number == "+19999999999"
        assert guest.email is None
        assert guest.password is None

    def test_register_duplicate_phone_raises_409(self, session: Session) -> None:
        """Should raise 409 when phone number already registered."""
        service = GuestService(session)
        service.register_guest_by_phone_number("Jane", "+19999999999")
        with pytest.raises(HTTPException) as exc_info:
            service.register_guest_by_phone_number("Other", "+19999999999")
        assert exc_info.value.status_code == 409


class TestGuestServiceRegisterByEmail:
    """Tests for GuestService.register_guest_by_email."""

    def test_register_creates_guest_with_hashed_password(self, session: Session) -> None:
        """Should create guest with email and hashed password."""
        service = GuestService(session)
        guest = service.register_guest_by_email(
            "Jane",
            "jane@test.com",
            "secret123",
        )
        assert guest.id is not None
        assert guest.name == "Jane"
        assert guest.email == "jane@test.com"
        assert guest.password is not None
        assert guest.password != "secret123"
        assert guest.phone_number == "email-jane@test.com"

    def test_register_duplicate_email_raises_409(self, session: Session) -> None:
        """Should raise 409 when email already registered."""
        service = GuestService(session)
        service.register_guest_by_email("Jane", "jane@test.com", "secret123")
        with pytest.raises(HTTPException) as exc_info:
            service.register_guest_by_email("Other", "jane@test.com", "other456")
        assert exc_info.value.status_code == 409
