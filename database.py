"""Database configuration and session management using SQLModel."""
from sqlmodel import SQLModel, create_engine, Session
from config import settings

# Create database engine
# Note: Use migrations (Alembic) instead of create_all for production
engine = create_engine(settings.database_url, echo=True)


def get_session():
    """Get database session."""
    with Session(engine) as session:
        yield session
