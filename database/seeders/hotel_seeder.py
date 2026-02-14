"""Hotel seeder."""

from app.models.hotel import Hotel
from app.repositories.hotel_repo import HotelRepository
from app.utils.slug import generate_unique_slug
from database.seeders.base_seeder import BaseSeeder


class HotelSeeder(BaseSeeder):
    """Seeder for Hotel records."""

    def get_model_name(self) -> str:
        return "Hotel"

    def seed(self, count: int = 10) -> list[Hotel]:
        hotel_repo = HotelRepository(self.session)
        hotels = []
        for _ in range(count):
            name = f"{self.fake.company()} Hotel"
            slug = generate_unique_slug(name, hotel_repo.slug_exists)
            hotel = Hotel(
                name=name,
                slug=slug,
                description=self.fake.paragraph(nb_sentences=3),
                contact_phone=self.fake.phone_number()[:20],
                contact_email=self.fake.email(),
                is_active=True,
            )
            self.session.add(hotel)
            hotels.append(hotel)
        self.session.commit()
        return hotels
