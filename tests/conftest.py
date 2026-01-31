"""Shared test fixtures and configuration."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.models.hotel import Hotel
from app.models.location import Location
from database import get_session
from main import app

# Ensure all models are imported for table creation
__all__ = ["Hotel", "Location"]


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
