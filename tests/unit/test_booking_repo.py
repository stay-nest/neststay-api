"""Unit tests for BookingRepository."""

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from app.models.booking import Booking, BookingStatus
from app.models.guest import Guest
from app.models.hotel import Hotel
from app.models.location import Location
from app.models.room_type import RoomType
from app.repositories.booking_repo import BookingRepository
from app.repositories.guest_repo import GuestRepository
from app.repositories.hotel_repo import HotelRepository
from app.repositories.location_repo import LocationRepository
from app.repositories.room_type_repo import RoomTypeRepository
from app.utils.slug import generate_unique_slug


@pytest.fixture
def db_booking_deps(session: Session):
    """Create hotel, location, room type, and guest for booking tests."""
    hotel_repo = HotelRepository(session)
    location_repo = LocationRepository(session)
    room_type_repo = RoomTypeRepository(session)
    guest_repo = GuestRepository(session)

    hotel = Hotel(
        name="Test Hotel",
        slug=generate_unique_slug("Test Hotel", hotel_repo.slug_exists),
        description="",
        contact_phone="+1234567890",
        contact_email="test@hotel.com",
    )
    hotel_repo.create(hotel)
    session.commit()
    session.refresh(hotel)

    location = Location(
        hotel_id=hotel.id,
        name="Test Location",
        slug=generate_unique_slug("Test Location", location_repo.slug_exists),
        address="123 Test St",
        city="Test City",
        state="TS",
        country="Testland",
        contact_phone="+1234567890",
    )
    location_repo.create(location)
    session.commit()
    session.refresh(location)

    room_type = RoomType(
        location_id=location.id,
        hotel_id=hotel.id,
        name="Deluxe",
        slug=generate_unique_slug("Deluxe", room_type_repo.slug_exists),
        base_price=Decimal("99.00"),
        total_inventory=5,
        max_occupancy=2,
        default_min_stay=1,
        max_advance_days=365,
    )
    room_type_repo.create(room_type)
    session.commit()
    session.refresh(room_type)

    guest = Guest(
        name="Jane",
        phone_number="+19999999999",
        email=None,
        password=None,
        is_active=True,
    )
    guest_repo.create(guest)
    session.commit()
    session.refresh(guest)

    return {
        "hotel": hotel,
        "location": location,
        "room_type": room_type,
        "guest": guest,
    }


def _make_booking(
    guest_id: int,
    room_type_id: int,
    location_id: int,
    hotel_id: int,
    slug: str = "booking-abc123",
    check_in: date | None = None,
    check_out: date | None = None,
) -> Booking:
    check_in = check_in or date(2026, 3, 1)
    check_out = check_out or date(2026, 3, 5)
    nights = (check_out - check_in).days
    price = Decimal("99.00")
    return Booking(
        slug=slug,
        guest_id=guest_id,
        room_type_id=room_type_id,
        location_id=location_id,
        hotel_id=hotel_id,
        check_in=check_in,
        check_out=check_out,
        num_rooms=1,
        num_guests=1,
        night_count=nights,
        price_per_night=price,
        total_price=price * nights,
        status=BookingStatus.PENDING,
    )


class TestBookingRepositoryCreate:
    """Tests for BookingRepository.create."""

    def test_create_persists_booking(
        self, session: Session, db_booking_deps: dict
    ) -> None:
        """Create should add booking to session (commit by caller)."""
        repo = BookingRepository(session)
        deps = db_booking_deps
        booking = _make_booking(
            deps["guest"].id,
            deps["room_type"].id,
            deps["location"].id,
            deps["hotel"].id,
        )
        created = repo.create(booking)
        session.commit()
        session.refresh(created)
        assert created.id is not None
        assert created.slug == "booking-abc123"
        assert created.guest_id == deps["guest"].id
        assert created.night_count == 4


class TestBookingRepositoryGetBySlug:
    """Tests for BookingRepository.get_by_slug."""

    def test_returns_booking_when_found(
        self, session: Session, db_booking_deps: dict
    ) -> None:
        """Should return booking when slug exists and not deleted."""
        repo = BookingRepository(session)
        deps = db_booking_deps
        booking = _make_booking(
            deps["guest"].id,
            deps["room_type"].id,
            deps["location"].id,
            deps["hotel"].id,
            slug="my-booking-xyz",
        )
        session.add(booking)
        session.commit()
        found = repo.get_by_slug("my-booking-xyz")
        assert found is not None
        assert found.slug == "my-booking-xyz"

    def test_returns_none_when_not_found(self, session: Session) -> None:
        """Should return None when slug does not exist."""
        repo = BookingRepository(session)
        found = repo.get_by_slug("nonexistent-slug")
        assert found is None

    def test_returns_none_when_soft_deleted(
        self, session: Session, db_booking_deps: dict
    ) -> None:
        """Should return None when booking is soft-deleted."""
        repo = BookingRepository(session)
        deps = db_booking_deps
        booking = _make_booking(
            deps["guest"].id,
            deps["room_type"].id,
            deps["location"].id,
            deps["hotel"].id,
            slug="deleted-booking",
        )
        session.add(booking)
        session.commit()
        session.refresh(booking)
        repo.soft_delete(booking)
        session.commit()
        found = repo.get_by_slug("deleted-booking")
        assert found is None


class TestBookingRepositoryGetByGuest:
    """Tests for BookingRepository.get_by_guest and count_by_guest."""

    def test_get_by_guest_returns_own_bookings_only(
        self, session: Session, db_booking_deps: dict
    ) -> None:
        """Should return only non-deleted bookings for guest, ordered by check_in desc."""
        repo = BookingRepository(session)
        deps = db_booking_deps
        g = deps["guest"]
        rt, loc, h = deps["room_type"], deps["location"], deps["hotel"]
        for i, (ci, co) in enumerate(
            [(date(2026, 4, 1), date(2026, 4, 3)), (date(2026, 3, 1), date(2026, 3, 4))]
        ):
            b = _make_booking(g.id, rt.id, loc.id, h.id, slug=f"b{i}", check_in=ci, check_out=co)
            session.add(b)
        session.commit()
        page = repo.get_by_guest(g.id, 0, 10)
        assert len(page) == 2
        assert page[0].check_in == date(2026, 4, 1)
        assert page[1].check_in == date(2026, 3, 1)
        assert repo.count_by_guest(g.id) == 2

    def test_get_by_guest_pagination(
        self, session: Session, db_booking_deps: dict
    ) -> None:
        """Should respect offset and limit."""
        repo = BookingRepository(session)
        deps = db_booking_deps
        g, rt, loc, h = deps["guest"], deps["room_type"], deps["location"], deps["hotel"]
        for i in range(4):
            b = _make_booking(
                g.id, rt.id, loc.id, h.id,
                slug=f"pag-{i}",
                check_in=date(2026, 5, i + 1),
                check_out=date(2026, 5, i + 2),
            )
            session.add(b)
        session.commit()
        page = repo.get_by_guest(g.id, 1, 2)
        assert len(page) == 2
        assert repo.count_by_guest(g.id) == 4


class TestBookingRepositoryUpdateAndSoftDelete:
    """Tests for BookingRepository.update and soft_delete."""

    def test_update_modifies_booking(
        self, session: Session, db_booking_deps: dict
    ) -> None:
        """update should persist changes after commit."""
        repo = BookingRepository(session)
        deps = db_booking_deps
        booking = _make_booking(
            deps["guest"].id,
            deps["room_type"].id,
            deps["location"].id,
            deps["hotel"].id,
            slug="upd-booking",
        )
        session.add(booking)
        session.commit()
        session.refresh(booking)
        booking.status = BookingStatus.CONFIRMED
        repo.update(booking)
        session.commit()
        session.refresh(booking)
        found = repo.get_by_slug("upd-booking")
        assert found is not None
        assert found.status == BookingStatus.CONFIRMED

    def test_soft_delete_excludes_from_get_by_slug(
        self, session: Session, db_booking_deps: dict
    ) -> None:
        """soft_delete should set deleted_at so get_by_slug returns None."""
        repo = BookingRepository(session)
        deps = db_booking_deps
        booking = _make_booking(
            deps["guest"].id,
            deps["room_type"].id,
            deps["location"].id,
            deps["hotel"].id,
            slug="del-booking",
        )
        session.add(booking)
        session.commit()
        session.refresh(booking)
        repo.soft_delete(booking)
        session.commit()
        assert repo.get_by_slug("del-booking") is None


class TestBookingRepositorySlugExists:
    """Tests for BookingRepository.slug_exists."""

    def test_slug_exists_true_when_present(
        self, session: Session, db_booking_deps: dict
    ) -> None:
        """Should return True when slug exists (non-deleted)."""
        repo = BookingRepository(session)
        deps = db_booking_deps
        booking = _make_booking(
            deps["guest"].id,
            deps["room_type"].id,
            deps["location"].id,
            deps["hotel"].id,
            slug="exists-slug",
        )
        session.add(booking)
        session.commit()
        assert repo.slug_exists("exists-slug") is True

    def test_slug_exists_false_when_absent(self, session: Session) -> None:
        """Should return False when slug does not exist."""
        repo = BookingRepository(session)
        assert repo.slug_exists("no-such-slug") is False

    def test_slug_exists_false_when_soft_deleted(
        self, session: Session, db_booking_deps: dict
    ) -> None:
        """Should return False when only matching booking is soft-deleted."""
        repo = BookingRepository(session)
        deps = db_booking_deps
        booking = _make_booking(
            deps["guest"].id,
            deps["room_type"].id,
            deps["location"].id,
            deps["hotel"].id,
            slug="gone-slug",
        )
        session.add(booking)
        session.commit()
        session.refresh(booking)
        repo.soft_delete(booking)
        session.commit()
        assert repo.slug_exists("gone-slug") is False
