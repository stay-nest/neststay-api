"""CLI entry point for database seeders."""

import argparse

from sqlmodel import Session

from database.database import engine
from database.seeders.guest_seeder import GuestSeeder
from database.seeders.hotel_seeder import HotelSeeder
from database.seeders.location_seeder import LocationSeeder
from database.seeders.room_type_seeder import RoomTypeSeeder

SEEDERS = {
    "hotel": HotelSeeder,
    "location": LocationSeeder,
    "room_type": RoomTypeSeeder,
    "guest": GuestSeeder,
}

# Order for "all": Hotel -> Location -> RoomType (FK); Guest independent
SEED_ORDER = ["hotel", "location", "room_type", "guest"]


def run_seeder(seeder_name: str, count: int, session: Session) -> None:
    """Run a single seeder."""
    seeder_class = SEEDERS.get(seeder_name)
    if not seeder_class:
        print(f"Unknown seeder: {seeder_name}")
        return

    seeder = seeder_class(session)
    print(f"Seeding {seeder.get_model_name()}...")
    records = seeder.seed(count)
    print(f"  Created {len(records)} {seeder.get_model_name()} records")


def main() -> None:
    parser = argparse.ArgumentParser(description="Database Seeder")
    parser.add_argument(
        "seeder",
        choices=[*SEEDERS, "all"],
        help="Which seeder to run (or 'all' for everything)",
    )
    parser.add_argument(
        "-c",
        "--count",
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
