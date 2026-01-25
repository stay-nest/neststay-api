"""Hotel repository for single-table database operations."""
from sqlmodel import Session, select, func
from app.models.hotel import Hotel


class HotelRepository:
    """Repository for Hotel entity operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def get_paginated(self, offset: int, limit: int) -> list[Hotel]:
        """Get paginated list of active hotels."""
        statement = (
            select(Hotel)
            .where(Hotel.is_active == True)
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def count(self) -> int:
        """Get total count of active hotels."""
        statement = select(func.count(Hotel.id)).where(Hotel.is_active == True)
        result = self.session.exec(statement).one()
        return result
