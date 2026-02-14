"""RoomType seeder."""

from decimal import Decimal
from typing import ClassVar

from sqlmodel import select

from app.models.location import Location
from app.models.room_type import RoomType
from app.repositories.room_type_repo import RoomTypeRepository
from app.utils.slug import generate_unique_slug
from database.seeders.base_seeder import BaseSeeder


class RoomTypeSeeder(BaseSeeder):
    """Seeder for RoomType records."""

    ROOM_NAMES: ClassVar[list[str]] = [
        "Standard",
        "Deluxe",
        "Suite",
        "Executive",
        "Presidential",
    ]

    def get_model_name(self) -> str:
        return "RoomType"

    def seed(
        self,
        count: int = 10,
        hotel_ids: list[int] | None = None,
        location_ids: list[int] | None = None,
    ) -> list[RoomType]:
        # Build list of (location_id, hotel_id) pairs so RoomType references are valid
        if location_ids is not None and hotel_ids is not None:
            if len(location_ids) != len(hotel_ids):
                raise ValueError("location_ids and hotel_ids must have same length")
            location_hotel_pairs = list(zip(location_ids, hotel_ids, strict=True))
        else:
            statement = select(Location).where(Location.is_active)
            locations = list(self.session.exec(statement).all())
            if not locations:
                raise ValueError("No locations found. Run LocationSeeder first.")
            location_hotel_pairs = [(loc.id, loc.hotel_id) for loc in locations]

        room_type_repo = RoomTypeRepository(self.session)
        room_types = []
        for _ in range(count):
            location_id, hotel_id = self.fake.random_element(location_hotel_pairs)
            name = f"{self.fake.random_element(self.ROOM_NAMES)}"
            slug = generate_unique_slug(name, room_type_repo.slug_exists)
            room_type = RoomType(
                location_id=location_id,
                hotel_id=hotel_id,
                name=name,
                slug=slug,
                description=self.fake.paragraph(nb_sentences=2),
                base_price=Decimal(str(self.fake.random_int(min=50, max=500))),
                total_inventory=self.fake.random_int(min=5, max=50),
                max_occupancy=self.fake.random_int(min=1, max=6),
                default_min_stay=1,
                max_advance_days=365,
                is_active=True,
            )
            self.session.add(room_type)
            room_types.append(room_type)
        self.session.commit()
        return room_types
