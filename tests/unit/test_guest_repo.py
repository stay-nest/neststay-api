"""Unit tests for GuestRepository."""

from sqlmodel import Session

from app.models.guest import Guest
from app.repositories.guest_repo import GuestRepository


class TestGuestRepositoryCreate:
    """Tests for GuestRepository.create."""

    def test_create_persists_guest(self, session: Session) -> None:
        """Create should add guest to session (commit by caller)."""
        repo = GuestRepository(session)
        guest = Guest(
            name="Jane",
            phone_number="+19999999999",
            email=None,
            password=None,
            is_active=True,
        )
        created = repo.create(guest)
        session.commit()
        session.refresh(created)
        assert created.id is not None
        assert created.name == "Jane"
        assert created.phone_number == "+19999999999"


class TestGuestRepositoryGetByPhoneNumber:
    """Tests for GuestRepository.get_guest_by_phone_number."""

    def test_returns_guest_when_found(self, session: Session) -> None:
        """Should return guest when phone number exists and active."""
        repo = GuestRepository(session)
        guest = Guest(
            name="Jane",
            phone_number="+19999999999",
            is_active=True,
        )
        session.add(guest)
        session.commit()
        found = repo.get_guest_by_phone_number("+19999999999")
        assert found is not None
        assert found.phone_number == "+19999999999"

    def test_returns_none_when_not_found(self, session: Session) -> None:
        """Should return None when phone number does not exist."""
        repo = GuestRepository(session)
        found = repo.get_guest_by_phone_number("+10000000000")
        assert found is None


class TestGuestRepositoryGetByEmail:
    """Tests for GuestRepository.get_guest_by_email."""

    def test_returns_guest_when_found(self, session: Session) -> None:
        """Should return guest when email exists and active."""
        repo = GuestRepository(session)
        guest = Guest(
            name="Jane",
            phone_number="+19999999999",
            email="jane@test.com",
            is_active=True,
        )
        session.add(guest)
        session.commit()
        found = repo.get_guest_by_email("jane@test.com")
        assert found is not None
        assert found.email == "jane@test.com"

    def test_returns_none_when_not_found(self, session: Session) -> None:
        """Should return None when email does not exist."""
        repo = GuestRepository(session)
        found = repo.get_guest_by_email("nobody@test.com")
        assert found is None


class TestGuestRepositoryGetById:
    """Tests for GuestRepository.get_guest_by_id."""

    def test_returns_guest_when_found(self, session: Session) -> None:
        """Should return guest when id exists and active."""
        repo = GuestRepository(session)
        guest = Guest(name="Jane", phone_number="+19999999999", is_active=True)
        session.add(guest)
        session.commit()
        session.refresh(guest)
        found = repo.get_guest_by_id(guest.id)
        assert found is not None
        assert found.id == guest.id

    def test_returns_none_when_not_found(self, session: Session) -> None:
        """Should return None when id does not exist."""
        repo = GuestRepository(session)
        found = repo.get_guest_by_id(99999)
        assert found is None


class TestGuestRepositoryGetPaginated:
    """Tests for GuestRepository.get_paginated and count."""

    def test_get_paginated_returns_page(self, session: Session) -> None:
        """Should return paginated list and count."""
        repo = GuestRepository(session)
        for i in range(5):
            session.add(
                Guest(
                    name=f"Guest {i}",
                    phone_number=f"+1999999999{i}",
                    is_active=True,
                )
            )
        session.commit()
        page = repo.get_paginated(1, 2)
        total = repo.count()
        assert len(page) == 2
        assert total == 5


class TestGuestRepositoryUpdateAndDelete:
    """Tests for GuestRepository.update_guest and delete_guest."""

    def test_update_guest_modifies_fields(self, session: Session) -> None:
        """update_guest should persist changes after commit."""
        repo = GuestRepository(session)
        guest = Guest(name="Jane", phone_number="+19999999999", is_active=True)
        session.add(guest)
        session.commit()
        session.refresh(guest)
        guest.name = "Jane Doe"
        repo.update_guest(guest)
        session.commit()
        session.refresh(guest)
        found = repo.get_guest_by_id(guest.id)
        assert found is not None
        assert found.name == "Jane Doe"

    def test_delete_guest_soft_deletes(self, session: Session) -> None:
        """delete_guest should soft-delete guest (is_active=False, not returned by get)."""
        repo = GuestRepository(session)
        guest = Guest(name="Jane", phone_number="+19999999999", is_active=True)
        session.add(guest)
        session.commit()
        session.refresh(guest)
        guest_id = guest.id
        repo.delete_guest(guest)
        session.commit()
        found = repo.get_guest_by_id(guest_id)
        assert found is None
