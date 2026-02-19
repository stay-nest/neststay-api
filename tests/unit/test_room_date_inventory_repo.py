"""Unit tests for RoomDateInventoryRepository."""

from datetime import date

import pytest
from sqlmodel import Session

from app.models.hotel import Hotel
from app.models.location import Location
from app.models.room_date_inventory import RoomDateInventory
from app.models.room_type import RoomType
from app.repositories.hotel_repo import HotelRepository
from app.repositories.location_repo import LocationRepository
from app.repositories.room_date_inventory_repo import RoomDateInventoryRepository
from app.repositories.room_type_repo import RoomTypeRepository
from app.utils.slug import generate_unique_slug


@pytest.fixture
def db_room_type(session: Session):
    """Create hotel, location, and room type for inventory tests."""
    hotel_repo = HotelRepository(session)
    location_repo = LocationRepository(session)
    room_type_repo = RoomTypeRepository(session)

    hotel = Hotel(
        name="Inv Hotel",
        slug=generate_unique_slug("Inv Hotel", hotel_repo.slug_exists),
        description="",
        contact_phone="+1234567890",
        contact_email="inv@hotel.com",
    )
    hotel_repo.create(hotel)
    session.commit()
    session.refresh(hotel)

    location = Location(
        hotel_id=hotel.id,
        name="Inv Location",
        slug=generate_unique_slug("Inv Location", location_repo.slug_exists),
        address="123 Inv St",
        city="City",
        state="ST",
        country="Country",
        contact_phone="+1234567890",
    )
    location_repo.create(location)
    session.commit()
    session.refresh(location)

    room_type = RoomType(
        location_id=location.id,
        hotel_id=hotel.id,
        name="Standard",
        slug=generate_unique_slug("Standard", room_type_repo.slug_exists),
        base_price=0,
        total_inventory=10,
        max_occupancy=2,
        default_min_stay=1,
        max_advance_days=365,
    )
    room_type_repo.create(room_type)
    session.commit()
    session.refresh(room_type)
    return room_type


class TestRoomDateInventoryEnsureRowsExist:
    """Tests for RoomDateInventoryRepository.ensure_rows_exist."""

    def test_creates_missing_rows_only(
        self, session: Session, db_room_type: RoomType
    ) -> None:
        """Should insert rows for dates that do not exist; end_date is exclusive."""
        repo = RoomDateInventoryRepository(session)
        rt_id = db_room_type.id
        total = db_room_type.total_inventory
        repo.ensure_rows_exist(rt_id, date(2026, 3, 1), date(2026, 3, 4), total)
        session.commit()
        rows = repo.get_for_date_range_with_lock(rt_id, date(2026, 3, 1), date(2026, 3, 4))
        assert len(rows) == 3
        assert all(r.total_rooms == total and r.booked_count == 0 for r in rows)
        assert [r.date for r in rows] == [
            date(2026, 3, 1),
            date(2026, 3, 2),
            date(2026, 3, 3),
        ]

    def test_does_not_overwrite_existing_rows(
        self, session: Session, db_room_type: RoomType
    ) -> None:
        """Should not change total_rooms for existing rows; new rows get new total_rooms."""
        repo = RoomDateInventoryRepository(session)
        rt_id = db_room_type.id
        repo.ensure_rows_exist(rt_id, date(2026, 4, 1), date(2026, 4, 3), 10)
        session.commit()
        repo.ensure_rows_exist(rt_id, date(2026, 4, 1), date(2026, 4, 4), 99)
        session.commit()
        rows = repo.get_for_date_range_with_lock(rt_id, date(2026, 4, 1), date(2026, 4, 4))
        assert len(rows) == 3
        assert rows[0].total_rooms == 10
        assert rows[1].total_rooms == 10
        assert rows[2].total_rooms == 99

    def test_empty_range_creates_nothing(
        self, session: Session, db_room_type: RoomType
    ) -> None:
        """When start_date >= end_date, no rows created."""
        repo = RoomDateInventoryRepository(session)
        rt_id = db_room_type.id
        repo.ensure_rows_exist(rt_id, date(2026, 3, 5), date(2026, 3, 5), 10)
        session.commit()
        rows = repo.get_for_date_range_with_lock(rt_id, date(2026, 3, 1), date(2026, 3, 10))
        assert len(rows) == 0


class TestRoomDateInventoryGetForDateRangeWithLock:
    """Tests for RoomDateInventoryRepository.get_for_date_range_with_lock."""

    def test_returns_rows_in_range_exclusive_end(
        self, session: Session, db_room_type: RoomType
    ) -> None:
        """Returns rows for [start_date, end_date); end_date excluded."""
        repo = RoomDateInventoryRepository(session)
        rt_id = db_room_type.id
        repo.ensure_rows_exist(rt_id, date(2026, 5, 1), date(2026, 5, 4), 5)
        session.commit()
        rows = repo.get_for_date_range_with_lock(rt_id, date(2026, 5, 1), date(2026, 5, 3))
        assert len(rows) == 2
        assert [r.date for r in rows] == [date(2026, 5, 1), date(2026, 5, 2)]

    def test_empty_range_returns_empty_list(
        self, session: Session, db_room_type: RoomType
    ) -> None:
        """When start_date >= end_date, returns []."""
        repo = RoomDateInventoryRepository(session)
        rows = repo.get_for_date_range_with_lock(
            db_room_type.id, date(2026, 6, 1), date(2026, 6, 1)
        )
        assert rows == []


class TestRoomDateInventoryCheckAvailability:
    """Tests for RoomDateInventoryRepository.check_availability."""

    def test_available_when_all_nights_have_rooms(
        self, session: Session, db_room_type: RoomType
    ) -> None:
        """Returns (True, min_available) when num_rooms <= min available."""
        repo = RoomDateInventoryRepository(session)
        rt_id = db_room_type.id
        repo.ensure_rows_exist(rt_id, date(2026, 7, 1), date(2026, 7, 4), 10)
        session.commit()
        available, min_avail = repo.check_availability(
            rt_id, date(2026, 7, 1), date(2026, 7, 4), 3
        )
        assert available is True
        assert min_avail == 10

    def test_not_available_when_insufficient(
        self, session: Session, db_room_type: RoomType
    ) -> None:
        """Returns (False, min_available) when num_rooms > min available."""
        repo = RoomDateInventoryRepository(session)
        rt_id = db_room_type.id
        repo.ensure_rows_exist(rt_id, date(2026, 8, 1), date(2026, 8, 4), 10)
        session.commit()
        rows = repo.get_for_date_range_with_lock(rt_id, date(2026, 8, 1), date(2026, 8, 4))
        repo.increment_booked(rows, 8)
        session.commit()
        available, min_avail = repo.check_availability(
            rt_id, date(2026, 8, 1), date(2026, 8, 4), 3
        )
        assert available is False
        assert min_avail == 2

    def test_no_rows_returns_zero_available(
        self, session: Session, db_room_type: RoomType
    ) -> None:
        """When no inventory rows exist for range, returns (False, 0)."""
        repo = RoomDateInventoryRepository(session)
        available, min_avail = repo.check_availability(
            db_room_type.id, date(2026, 9, 1), date(2026, 9, 3), 1
        )
        assert available is False
        assert min_avail == 0

    def test_empty_range_returns_true_zero(
        self, session: Session, db_room_type: RoomType
    ) -> None:
        """When start_date >= end_date, returns (True, 0) per implementation."""
        repo = RoomDateInventoryRepository(session)
        available, min_avail = repo.check_availability(
            db_room_type.id, date(2026, 10, 1), date(2026, 10, 1), 1
        )
        assert available is True
        assert min_avail == 0


class TestRoomDateInventoryIncrementDecrementBooked:
    """Tests for increment_booked and decrement_booked."""

    def test_increment_booked_increases_count(
        self, session: Session, db_room_type: RoomType
    ) -> None:
        """increment_booked adds count to each row."""
        repo = RoomDateInventoryRepository(session)
        rt_id = db_room_type.id
        repo.ensure_rows_exist(rt_id, date(2026, 11, 1), date(2026, 11, 4), 10)
        session.commit()
        rows = repo.get_for_date_range_with_lock(rt_id, date(2026, 11, 1), date(2026, 11, 4))
        repo.increment_booked(rows, 2)
        session.commit()
        rows_after = repo.get_for_date_range_with_lock(
            rt_id, date(2026, 11, 1), date(2026, 11, 4)
        )
        assert all(r.booked_count == 2 for r in rows_after)

    def test_decrement_booked_decreases_count(
        self, session: Session, db_room_type: RoomType
    ) -> None:
        """decrement_booked subtracts count; end_date exclusive."""
        repo = RoomDateInventoryRepository(session)
        rt_id = db_room_type.id
        repo.ensure_rows_exist(rt_id, date(2026, 12, 1), date(2026, 12, 5), 10)
        session.commit()
        rows = repo.get_for_date_range_with_lock(rt_id, date(2026, 12, 1), date(2026, 12, 5))
        repo.increment_booked(rows, 3)
        session.commit()
        repo.decrement_booked(rt_id, date(2026, 12, 1), date(2026, 12, 4), 2)
        session.commit()
        updated = repo.get_for_date_range_with_lock(rt_id, date(2026, 12, 1), date(2026, 12, 5))
        assert [r.booked_count for r in updated] == [1, 1, 1, 3]

    def test_decrement_booked_does_not_go_below_zero(
        self, session: Session, db_room_type: RoomType
    ) -> None:
        """decrement_booked clamps to 0 (range is 2 nights: 1st and 2nd)."""
        repo = RoomDateInventoryRepository(session)
        rt_id = db_room_type.id
        repo.ensure_rows_exist(rt_id, date(2027, 1, 1), date(2027, 1, 3), 10)
        session.commit()
        repo.decrement_booked(rt_id, date(2027, 1, 1), date(2027, 1, 3), 5)
        session.commit()
        rows = repo.get_for_date_range_with_lock(rt_id, date(2027, 1, 1), date(2027, 1, 3))
        assert [r.booked_count for r in rows] == [0, 0]
