# Booking System Implementation Plan

## Overview

Implement a scalable booking system where guests can book rooms (by RoomType) at a Location for a date range. Uses a **date-level inventory table** for O(days) availability checks instead of scanning all bookings.

**Scope:** Guest-facing booking + public availability endpoints. Admin routes deferred.

## Architecture Decision: Date-Level Inventory

Instead of computing availability by counting overlapping bookings (slow at scale), we maintain a `RoomDateInventory` table with one row per (room_type, date). This gives us:

- **Fast availability**: `SELECT MIN(total_rooms - booked_count) WHERE room_type_id=X AND date BETWEEN check_in AND check_out-1`
- **Concurrency safety**: `SELECT ... FOR UPDATE` on inventory rows prevents double-booking
- **Simple cancellation**: just decrement `booked_count`

---

## Phase 1: Models & Migration

**Decisions:**
- Default booking status: `PENDING`
- Monetary fields: use `Decimal` with `max_digits`/`decimal_places` as per `RoomType.base_price`

### 1.1 BookingStatus Enum

**File:** `app/models/booking.py`

```python
class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
```

**State transitions:**
```
PENDING → CONFIRMED → CHECKED_IN → CHECKED_OUT
  ↓           ↓
CANCELLED   CANCELLED / NO_SHOW
```

### 1.2 Booking Model

**File:** `app/models/booking.py`

| Field | Type | Notes |
|---|---|---|
| id | int (PK) | |
| slug | str (unique, indexed) | Public identifier |
| guest_id | int (FK → guests) | Indexed |
| room_type_id | int (FK → room_types) | Indexed |
| location_id | int (FK → locations) | Denormalized for fast queries |
| hotel_id | int (FK → hotels) | Denormalized for fast queries |
| check_in | date | |
| check_out | date | |
| num_rooms | int (default=1) | |
| num_guests | int (default=1) | |
| night_count | int | Pre-computed |
| price_per_night | Decimal(10,2) | Snapshot at booking time |
| total_price | Decimal(12,2) | Snapshot at booking time |
| status | str | BookingStatus enum |
| special_requests | str (nullable) | |
| cancellation_reason | str (nullable) | |
| cancelled_at | datetime (nullable) | |
| created_at | datetime | |
| updated_at | datetime | |
| deleted_at | datetime (nullable) | Soft delete |

Relationships: guest, room_type, location, hotel

### 1.3 RoomDateInventory Model

**File:** `app/models/room_date_inventory.py`

| Field | Type | Notes |
|---|---|---|
| id | int (PK) | |
| room_type_id | int (FK → room_types) | |
| date | date | |
| total_rooms | int | From room_type.total_inventory |
| booked_count | int (default=0) | |

- Unique constraint on `(room_type_id, date)`
- Composite index on `(room_type_id, date)` for range queries
- Rows created **lazily** — only when a booking touches that date

### 1.4 Update Existing Models

Add `bookings` relationship to:
- `app/models/guest.py`
- `app/models/room_type.py` (also add `inventory_dates`)
- `app/models/location.py`
- `app/models/hotel.py`

### 1.5 Register Models

- `database/alembic/env.py` — import Booking, RoomDateInventory
- `tests/conftest.py` — import new models for SQLite table creation

### 1.6 Generate Migration

```bash
make migrate-make MESSAGE="add booking and room date inventory tables"
make migrate
```

---

## Phase 2: Repositories

### 2.1 BookingRepository

**File:** `app/repositories/booking_repo.py`

```python
class BookingRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, booking: Booking) -> Booking
    def get_by_slug(self, slug: str) -> Booking | None
    def get_by_guest(self, guest_id: int, offset: int, limit: int) -> list[Booking]
    def count_by_guest(self, guest_id: int) -> int
    def update(self, booking: Booking) -> Booking
    def soft_delete(self, booking: Booking) -> Booking
    def slug_exists(self, slug: str) -> bool
```

### 2.2 RoomDateInventoryRepository

**File:** `app/repositories/room_date_inventory_repo.py`

```python
class RoomDateInventoryRepository:
    def __init__(self, session: Session):
        self.session = session

    def ensure_rows_exist(
        self, room_type_id: int, start_date: date, end_date: date, total_rooms: int
    ) -> None
        # Lazy creation: insert missing rows for the date range

    def get_for_date_range_with_lock(
        self, room_type_id: int, start_date: date, end_date: date
    ) -> list[RoomDateInventory]
        # SELECT ... FOR UPDATE for concurrency safety

    def check_availability(
        self, room_type_id: int, start_date: date, end_date: date, num_rooms: int
    ) -> tuple[bool, int]
        # Returns (is_available, min_rooms_available) — read-only, no lock

    def increment_booked(self, rows: list[RoomDateInventory], count: int) -> None

    def decrement_booked(
        self, room_type_id: int, start_date: date, end_date: date, count: int
    ) -> None
```

---

## Phase 3: Schemas

**File:** `app/schemas/booking_schema.py`

```python
class BookingCreate(BaseModel):
    room_type_id: int
    check_in: date
    check_out: date
    num_rooms: int = 1
    num_guests: int = 1
    special_requests: str | None = None

class BookingRead(BaseModel):
    slug: str
    guest_id: int
    room_type_id: int
    location_id: int
    hotel_id: int
    check_in: date
    check_out: date
    num_rooms: int
    num_guests: int
    night_count: int
    price_per_night: Decimal
    total_price: Decimal
    status: str
    special_requests: str | None
    created_at: datetime
    updated_at: datetime

class BookingCancel(BaseModel):
    reason: str | None = None

class AvailabilityResponse(BaseModel):
    room_type_slug: str
    room_type_name: str
    available: bool
    rooms_available: int
    price_per_night: Decimal
    total_price: Decimal
    nights: int

class LocationAvailabilityResponse(BaseModel):
    location_slug: str
    location_name: str
    check_in: date
    check_out: date
    room_types: list[AvailabilityResponse]
```

---

## Phase 4: Booking Service

**File:** `app/services/booking_service.py`

### 4.1 create_booking — Core Transaction Flow

```python
def create_booking(self, guest_id: int, data: BookingCreate) -> Booking:
    # 1. Validate room_type exists and is active
    # 2. Validate dates (check_out > check_in, min stay, max advance, not in past)
    # 3. Ensure RoomDateInventory rows exist (lazy creation)
    # 4. session.flush() so rows are visible
    # 5. SELECT ... FOR UPDATE on inventory rows (row-level lock)
    # 6. Check MIN(total_rooms - booked_count) >= num_rooms
    # 7. If not available → raise 409 Conflict
    # 8. Increment booked_count for each date
    # 9. Create Booking record with snapshot pricing
    # 10. session.commit() (releases locks)
    # 11. Return booking
```

### 4.2 cancel_booking

```python
def cancel_booking(self, slug: str, guest_id: int, reason: str | None) -> Booking:
    # 1. Get booking by slug, verify ownership
    # 2. Verify status is PENDING or CONFIRMED
    # 3. Decrement booked_count for each date in range
    # 4. Set status=CANCELLED, cancellation_reason, cancelled_at
    # 5. Commit
```

### 4.3 Other Methods

```python
def check_availability(self, room_type_id, check_in, check_out, num_rooms) -> AvailabilityResponse
def get_booking_by_slug(self, slug: str) -> Booking
def list_guest_bookings(self, guest_id: int, page: int, page_size: int) -> PaginatedResponse
def get_location_availability(self, location_slug, check_in, check_out) -> LocationAvailabilityResponse
```

---

## Phase 5: Routes & Registration

### 5.1 Availability Routes (Public)

**File:** `app/routes/availability.py`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/availability/{room_type_slug}?check_in=&check_out=&num_rooms=1` | Check single room type |
| GET | `/availability/location/{location_slug}?check_in=&check_out=` | All room types at location |

### 5.2 Booking Routes (Authenticated)

**File:** `app/routes/booking.py`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/bookings/` | Create a booking |
| GET | `/bookings/` | List my bookings (paginated) |
| GET | `/bookings/{slug}` | Get booking details |
| POST | `/bookings/{slug}/cancel` | Cancel a booking |

### 5.3 Register in main.py

```python
from app.routes import booking as booking_routes
from app.routes import availability as availability_routes

app.include_router(booking_routes.router)
app.include_router(availability_routes.router)
```

---

## Phase 6: Tests

**File:** `tests/api/test_booking.py`

Test coverage:
- Create booking with valid data → 201, inventory decremented
- Create booking with invalid dates (past, check_out <= check_in, below min stay) → 422
- Create booking when no availability → 409
- Cancel booking → inventory restored, status=cancelled
- Cancel already cancelled booking → 422
- Cancel another guest's booking → 403
- List my bookings → only returns own bookings
- Get booking by slug → returns detail

**File:** `tests/api/test_availability.py`

Test coverage:
- Check availability with no bookings → all rooms available
- Check availability after partial booking → reduced count
- Check availability when fully booked → available=false
- Location availability → returns all room types

---

## Concurrency Safety Details

The `SELECT ... FOR UPDATE` on `RoomDateInventory` rows ensures:

1. Request A locks inventory rows for room_type=5, dates Mar 1-4
2. Request B tries same rows → **blocks** until A commits
3. A increments booked_count, commits → locks released
4. B proceeds, sees updated counts, gets 409 if no rooms left

Lock granularity is per (room_type, date) row, so different room types or non-overlapping dates never block each other. Lock hold time is minimal (milliseconds).

For read-only availability checks (search/browse), no locking is used — slight staleness is acceptable for display.

**SQLite test compatibility:** SQLAlchemy silently ignores `FOR UPDATE` on SQLite, so no conditional code needed.

---

## Files Summary

### New Files

| File | Purpose |
|------|---------|
| `app/models/booking.py` | Booking model + BookingStatus enum |
| `app/models/room_date_inventory.py` | RoomDateInventory model |
| `app/repositories/booking_repo.py` | Booking repository |
| `app/repositories/room_date_inventory_repo.py` | Inventory repository |
| `app/schemas/booking_schema.py` | Request/response schemas |
| `app/services/booking_service.py` | Booking business logic |
| `app/routes/booking.py` | Guest booking endpoints |
| `app/routes/availability.py` | Public availability endpoints |
| `tests/api/test_booking.py` | Booking tests |
| `tests/api/test_availability.py` | Availability tests |

### Modified Files

| File | Change |
|------|--------|
| `app/models/guest.py` | Add `bookings` relationship |
| `app/models/room_type.py` | Add `bookings` + `inventory_dates` relationships |
| `app/models/location.py` | Add `bookings` relationship |
| `app/models/hotel.py` | Add `bookings` relationship |
| `database/alembic/env.py` | Import new models |
| `tests/conftest.py` | Import new models, add booking fixtures |
| `main.py` | Register new routers |

## Verification

1. `make migrate` — apply new tables
2. `make test` — all tests pass
3. Test availability: `GET /availability/{slug}?check_in=2026-03-01&check_out=2026-03-05`
4. Test booking: `POST /bookings/` with auth token
5. Verify inventory decremented after booking
6. Test cancel: `POST /bookings/{slug}/cancel` — inventory restored
