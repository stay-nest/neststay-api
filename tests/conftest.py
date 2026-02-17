"""Shared test fixtures and configuration."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.models.booking import Booking
from app.models.guest import Guest
from app.models.hotel import Hotel
from app.models.location import Location
from app.models.location_image import LocationImage
from app.models.room_date_inventory import RoomDateInventory
from app.models.room_type import RoomType
from app.utils.slug import generate_unique_slug
from database import get_session
from main import app

# Ensure all models are imported for table creation
__all__ = [
    "Booking",
    "Guest",
    "Hotel",
    "Location",
    "LocationImage",
    "RoomDateInventory",
    "RoomType",
]


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """Create a new database session for each test.

    Uses SQLite in-memory database with StaticPool to ensure
    the same connection is reused across the session.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database session override.

    The session dependency is overridden to use our test session,
    ensuring all requests use the in-memory SQLite database.
    """

    def get_session_override() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_hotel_data() -> dict:
    """Sample hotel data for creating test hotels."""
    return {
        "name": "Test Hotel",
        "description": "A test hotel description",
        "contact_phone": "+1234567890",
        "contact_email": "test@hotel.com",
    }


@pytest.fixture
def created_hotel(client: TestClient, sample_hotel_data: dict) -> dict:
    """Create a hotel and return its data."""
    response = client.post("/hotels/", json=sample_hotel_data)
    return response.json()


@pytest.fixture
def sample_guest_register_phone() -> dict:
    """Sample guest registration data (phone flow)."""
    return {"name": "Test Guest", "phone_number": "+1234567890"}


@pytest.fixture
def sample_guest_register_email() -> dict:
    """Sample guest registration data (email flow)."""
    return {
        "name": "Email Guest",
        "email": "guest@test.com",
        "password": "secret123",
    }


@pytest.fixture
def created_guest(
    client: TestClient, sample_guest_register_phone: dict
) -> dict:
    """Create a guest via phone registration and return its data."""
    response = client.post("/guest/register", json=sample_guest_register_phone)
    return response.json()


@pytest.fixture
def db_hotel_and_location(session: Session, sample_hotel_data: dict):
    """Create hotel and location directly in DB for tests that need location_id."""
    from app.models.hotel import Hotel
    from app.models.location import Location
    from app.repositories.hotel_repo import HotelRepository
    from app.repositories.location_repo import LocationRepository

    hotel_repo = HotelRepository(session)
    location_repo = LocationRepository(session)

    hotel = Hotel(
        name=sample_hotel_data["name"],
        slug=generate_unique_slug(
            name=sample_hotel_data["name"],
            check_exists=hotel_repo.slug_exists,
        ),
        description=sample_hotel_data.get("description", ""),
        contact_phone=sample_hotel_data["contact_phone"],
        contact_email=sample_hotel_data.get("contact_email"),
    )
    hotel_repo.create(hotel)
    session.commit()
    session.refresh(hotel)

    location = Location(
        hotel_id=hotel.id,
        name="Test Location",
        slug=generate_unique_slug(
            name="Test Location",
            check_exists=location_repo.slug_exists,
        ),
        address="123 Test St",
        city="Test City",
        state="TS",
        country="Testland",
        contact_phone="+1234567890",
    )
    location_repo.create(location)
    session.commit()
    session.refresh(location)

    return {"hotel": hotel, "location": location}


@pytest.fixture
def auth_guest(client: TestClient, sample_guest_register_email: dict) -> dict:
    """Create a guest with email+password for auth tests."""
    response = client.post("/guest/register", json=sample_guest_register_email)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def auth_tokens(
    client: TestClient, auth_guest: dict, sample_guest_register_email: dict
) -> dict:
    """Login and return token response."""
    response = client.post(
        "/auth/login",
        json={
            "email": sample_guest_register_email["email"],
            "password": sample_guest_register_email["password"],
        },
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def auth_headers(auth_tokens: dict) -> dict:
    """Headers with Bearer token for authenticated requests."""
    return {"Authorization": f"Bearer {auth_tokens['access_token']}"}


@pytest.fixture
def sample_room_type_data(db_hotel_and_location: dict) -> dict:
    """Sample room type data. Requires db_hotel_and_location for location_id."""
    location = db_hotel_and_location["location"]
    return {
        "location_id": location.id,
        "name": "Deluxe Suite",
        "description": "A luxurious suite",
        "base_price": "149.99",
        "total_inventory": 10,
        "max_occupancy": 4,
        "default_min_stay": 1,
        "max_advance_days": 365,
    }
