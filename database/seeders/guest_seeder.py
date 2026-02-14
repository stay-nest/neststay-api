"""Guest seeder."""

from app.models.guest import Guest
from app.utils.password import hash_password
from database.seeders.base_seeder import BaseSeeder


class GuestSeeder(BaseSeeder):
    """Seeder for Guest records."""

    def get_model_name(self) -> str:
        return "Guest"

    def seed(self, count: int = 10) -> list[Guest]:
        guests = []
        for _ in range(count):
            guest = Guest(
                name=self.fake.name(),
                email=self.fake.unique.email(),
                phone_number=self.fake.unique.phone_number()[:20],
                password=hash_password("password123"),
                is_active=True,
            )
            self.session.add(guest)
            guests.append(guest)
        self.session.commit()
        return guests
