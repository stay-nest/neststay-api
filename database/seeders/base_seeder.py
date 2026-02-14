"""Abstract base class for database seeders."""

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

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name for logging."""
