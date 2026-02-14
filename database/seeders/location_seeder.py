"""Location seeder."""

from sqlmodel import select

from app.models.hotel import Hotel
from app.models.location import Location
from app.repositories.location_repo import LocationRepository
from app.utils.slug import generate_unique_slug
from database.seeders.base_seeder import BaseSeeder


class LocationSeeder(BaseSeeder):
    """Seeder for Location records."""

    def get_model_name(self) -> str:
        return "Location"

    def seed(
        self, count: int = 10, hotel_ids: list[int] | None = None
    ) -> list[Location]:
        if not hotel_ids:
            statement = select(Hotel).where(Hotel.is_active)
            hotels = list(self.session.exec(statement).all())
            if not hotels:
                raise ValueError("No hotels found. Run HotelSeeder first.")
            hotel_ids = [h.id for h in hotels]

        location_repo = LocationRepository(self.session)
        locations = []
        for _ in range(count):
            name = self.fake.city()
            slug = generate_unique_slug(name, location_repo.slug_exists)
            location = Location(
                hotel_id=self.fake.random_element(hotel_ids),
                name=name,
                slug=slug,
                description=self.fake.paragraph(nb_sentences=2),
                address=self.fake.street_address(),
                city=self.fake.city(),
                state=self.fake.state(),
                country=self.fake.country(),
                contact_phone=self.fake.phone_number()[:20],
                contact_email=self.fake.email(),
                is_active=True,
            )
            self.session.add(location)
            locations.append(location)
        self.session.commit()
        return locations
