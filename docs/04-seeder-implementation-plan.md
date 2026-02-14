# Database Seeder Implementation Plan

## Overview

Implement a database seeding system using Faker library to populate the database with realistic test data. The seeder will support seeding individual tables or all tables at once, with configurable record counts.

## Dependencies

| Package | Purpose |
|---------|---------|
| `faker` | Generate realistic fake data (names, addresses, emails, etc.) |

## Seeder Architecture

```
database/
└── seeders/
    ├── __init__.py
    ├── base_seeder.py      # Abstract base class
    ├── location_seeder.py  # Location seeder
    ├── hotel_seeder.py     # Hotel seeder (depends on Location)
    ├── room_type_seeder.py # RoomType seeder (depends on Hotel)
    ├── guest_seeder.py     # Guest seeder
    └── run.py              # CLI entry point
```

## Seeding Order (Dependencies)

Seeders must run in order due to foreign key relationships. **Note:** The codebase schema is Hotel → Location → RoomType (Location belongs to Hotel; RoomType belongs to both Hotel and Location).

1. **Hotel** - No dependencies
2. **Location** - Requires Hotel
3. **RoomType** - Requires Hotel and Location
4. **Guest** - No dependencies (can run anytime)

## Implementation Steps

### 1. Install Dependencies

```bash
uv add faker --dev
```

### 2. Create Base Seeder Class

**File:** `database/seeders/base_seeder.py`

```python
from abc import ABC, abstractmethod
from faker import Faker
from sqlmodel import Session

class BaseSeeder(ABC):
    """Abstract base class for all seeders."""

    def __init__(self, session: Session):
        self.session = session
        self.fake = Faker()

    @abstractmethod
    def seed(self, count: int = 10) -> list:
        """Seed the database with fake records. Returns created records."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name for logging."""
        pass
```

### 3. Create Location Seeder

**File:** `database/seeders/location_seeder.py`

```python
from database.seeders.base_seeder import BaseSeeder
from app.models.location import Location

class LocationSeeder(BaseSeeder):
    def get_model_name(self) -> str:
        return "Location"

    def seed(self, count: int = 10) -> list[Location]:
        locations = []
        for _ in range(count):
            location = Location(
                name=self.fake.city(),
                state=self.fake.state(),
                country=self.fake.country(),
            )
            self.session.add(location)
            locations.append(location)
        self.session.commit()
        return locations
```

### 4. Create Hotel Seeder

**File:** `database/seeders/hotel_seeder.py`

```python
from database.seeders.base_seeder import BaseSeeder
from app.models.hotel import Hotel
from app.models.location import Location

class HotelSeeder(BaseSeeder):
    def get_model_name(self) -> str:
        return "Hotel"

    def seed(self, count: int = 10, location_ids: list[int] | None = None) -> list[Hotel]:
        # If no location_ids provided, fetch existing locations
        if not location_ids:
            locations = self.session.query(Location).all()
            if not locations:
                raise ValueError("No locations found. Run LocationSeeder first.")
            location_ids = [loc.id for loc in locations]

        hotels = []
        for _ in range(count):
            hotel = Hotel(
                name=f"{self.fake.company()} Hotel",
                description=self.fake.paragraph(nb_sentences=3),
                address=self.fake.street_address(),
                location_id=self.fake.random_element(location_ids),
            )
            self.session.add(hotel)
            hotels.append(hotel)
        self.session.commit()
        return hotels
```

### 5. Create RoomType Seeder

**File:** `database/seeders/room_type_seeder.py`

```python
from decimal import Decimal
from database.seeders.base_seeder import BaseSeeder
from app.models.room_type import RoomType
from app.models.hotel import Hotel

class RoomTypeSeeder(BaseSeeder):
    ROOM_TYPES = ["Standard", "Deluxe", "Suite", "Executive", "Presidential"]

    def get_model_name(self) -> str:
        return "RoomType"

    def seed(self, count: int = 10, hotel_ids: list[int] | None = None) -> list[RoomType]:
        if not hotel_ids:
            hotels = self.session.query(Hotel).all()
            if not hotels:
                raise ValueError("No hotels found. Run HotelSeeder first.")
            hotel_ids = [h.id for h in hotels]

        room_types = []
        for _ in range(count):
            room_type = RoomType(
                name=self.fake.random_element(self.ROOM_TYPES),
                description=self.fake.paragraph(nb_sentences=2),
                base_price=Decimal(str(self.fake.random_int(min=50, max=500))),
                max_occupancy=self.fake.random_int(min=1, max=6),
                hotel_id=self.fake.random_element(hotel_ids),
            )
            self.session.add(room_type)
            room_types.append(room_type)
        self.session.commit()
        return room_types
```

### 6. Create Guest Seeder

**File:** `database/seeders/guest_seeder.py`

```python
from database.seeders.base_seeder import BaseSeeder
from app.models.guest import Guest
from app.utils.password import hash_password

class GuestSeeder(BaseSeeder):
    def get_model_name(self) -> str:
        return "Guest"

    def seed(self, count: int = 10) -> list[Guest]:
        guests = []
        for _ in range(count):
            guest = Guest(
                name=self.fake.name(),
                email=self.fake.unique.email(),
                phone_number=self.fake.unique.phone_number()[:15],
                password_hash=hash_password("password123"),
            )
            self.session.add(guest)
            guests.append(guest)
        self.session.commit()
        return guests
```

### 7. Create Seeder Runner

**File:** `database/seeders/run.py`

```python
import argparse
from sqlmodel import Session
from database.database import engine
from database.seeders.location_seeder import LocationSeeder
from database.seeders.hotel_seeder import HotelSeeder
from database.seeders.room_type_seeder import RoomTypeSeeder
from database.seeders.guest_seeder import GuestSeeder

SEEDERS = {
    "location": LocationSeeder,
    "hotel": HotelSeeder,
    "room_type": RoomTypeSeeder,
    "guest": GuestSeeder,
}

# Order matters for 'all' command
SEED_ORDER = ["location", "hotel", "room_type", "guest"]


def run_seeder(seeder_name: str, count: int, session: Session):
    """Run a single seeder."""
    seeder_class = SEEDERS.get(seeder_name)
    if not seeder_class:
        print(f"Unknown seeder: {seeder_name}")
        return

    seeder = seeder_class(session)
    print(f"Seeding {seeder.get_model_name()}...")
    records = seeder.seed(count)
    print(f"  Created {len(records)} {seeder.get_model_name()} records")


def main():
    parser = argparse.ArgumentParser(description="Database Seeder")
    parser.add_argument(
        "seeder",
        choices=list(SEEDERS.keys()) + ["all"],
        help="Which seeder to run (or 'all' for everything)",
    )
    parser.add_argument(
        "-c", "--count",
        type=int,
        default=10,
        help="Number of records to create (default: 10)",
    )
    args = parser.parse_args()

    with Session(engine) as session:
        if args.seeder == "all":
            for seeder_name in SEED_ORDER:
                run_seeder(seeder_name, args.count, session)
        else:
            run_seeder(args.seeder, args.count, session)

    print("Seeding complete!")


if __name__ == "__main__":
    main()
```

### 8. Create Package Init

**File:** `database/seeders/__init__.py`

```python
from database.seeders.base_seeder import BaseSeeder
from database.seeders.location_seeder import LocationSeeder
from database.seeders.hotel_seeder import HotelSeeder
from database.seeders.room_type_seeder import RoomTypeSeeder
from database.seeders.guest_seeder import GuestSeeder

__all__ = [
    "BaseSeeder",
    "LocationSeeder",
    "HotelSeeder",
    "RoomTypeSeeder",
    "GuestSeeder",
]
```

### 9. Add Makefile Commands

**File:** `Makefile` (add these commands)

```makefile
# Seed all tables
seed:
	python -m database.seeders.run all

# Seed specific table
seed-locations:
	python -m database.seeders.run location

seed-hotels:
	python -m database.seeders.run hotel

seed-room-types:
	python -m database.seeders.run room_type

seed-guests:
	python -m database.seeders.run guest
```

## Files to Create/Modify

| File | Action |
|------|--------|
| `pyproject.toml` | Add faker as dev dependency |
| `database/seeders/__init__.py` | Create (package init) |
| `database/seeders/base_seeder.py` | Create (abstract base class) |
| `database/seeders/location_seeder.py` | Create (location seeder) |
| `database/seeders/hotel_seeder.py` | Create (hotel seeder) |
| `database/seeders/room_type_seeder.py` | Create (room type seeder) |
| `database/seeders/guest_seeder.py` | Create (guest seeder) |
| `database/seeders/run.py` | Create (CLI runner) |
| `Makefile` | Add seed commands |

## Usage Examples

```bash
# Seed all tables with 10 records each
make seed

# Seed all tables with custom count
python -m database.seeders.run all -c 50

# Seed only locations
make seed-locations

# Seed only hotels with 20 records
python -m database.seeders.run hotel -c 20
```

## Future Enhancements

- Add `--fresh` flag to truncate tables before seeding
- Add `--env` flag to prevent accidental production seeding
- Create factory classes for use in tests
- Add progress bar for large seed counts
- Support seeding from JSON/YAML fixture files

## Verification

1. Run `uv add faker --dev` to install dependency
2. Create all seeder files as specified
3. Run `make seed` to seed all tables
4. Verify data in database:
   ```bash
   # Connect to MySQL and check counts
   mysql -u user -p database -e "SELECT COUNT(*) FROM locations;"
   mysql -u user -p database -e "SELECT COUNT(*) FROM hotels;"
   ```
5. Run `make test` to ensure seeders don't break existing tests

---

## Implementation Notes (Schema Alignment)

The plan’s code snippets assume an older schema. Implementation will align with current models:

| Item | Plan assumption | Actual codebase |
|------|-----------------|-----------------|
| **Order** | Location → Hotel → RoomType | **Hotel → Location → RoomType** (Location has `hotel_id`) |
| **Hotel** | Has `address`, `location_id` | Has `slug`, `contact_phone`, `contact_email`; no address/location_id |
| **Location** | Only name, state, country | Has `hotel_id`, `slug`, `name`, `description`, `address`, `city`, `state`, `country`, `contact_phone`, `contact_email` |
| **RoomType** | Only hotel_id | Has both `hotel_id` and `location_id`, plus `slug`, `total_inventory`, `default_min_stay`, `max_advance_days` |
| **Guest** | Field `password_hash` | Field is **`password`** (store hashed value there) |
| **Slugs** | Not in plan | Hotel, Location, RoomType require unique `slug`; use `app.utils.slug.generate_unique_slug` with repo’s `slug_exists` in seeders |
