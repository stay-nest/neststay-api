# Architecture: Repository and Service Layer Pattern

This document describes the layered architecture used for handling database operations in the NestStay API.

## Overview

```
routes/ (endpoints)
   ↓
services/ (business logic, transactions)
   ↓
repositories/ (single-table DB operations)
   ↓
models/ (SQLModel entities)
```

## Layer Responsibilities

### Repositories

Repositories handle database operations for a **single table only**. They:

- Contain CRUD operations for one model
- Never call other repositories
- Never commit transactions (caller handles this)
- Receive a `Session` via constructor

```python
# app/repositories/location_repo.py
from sqlmodel import Session
from app.models import Location
from app.schemas.location_schema import LocationCreate

class LocationRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: LocationCreate) -> Location:
        location = Location.model_validate(data)
        self.session.add(location)
        return location

    def get_by_id(self, location_id: int) -> Location | None:
        return self.session.get(Location, location_id)

    def get_all(self) -> list[Location]:
        return self.session.exec(select(Location)).all()
```

### Services

Services handle **business logic** that may span multiple tables. They:

- Coordinate multiple repositories
- Own the transaction (call `commit()`)
- Contain business rules and validations beyond schema validation
- Are used when an operation affects more than one table

```python
# app/services/location_service.py
from sqlmodel import Session
from app.repositories.location_repo import LocationRepository
from app.repositories.hotel_repo import HotelRepository
from app.schemas.location_schema import LocationCreate
from app.models import Location

class LocationService:
    def __init__(self, session: Session):
        self.session = session
        self.location_repo = LocationRepository(session)
        self.hotel_repo = HotelRepository(session)

    def create(self, data: LocationCreate) -> Location:
        # Create the location
        location = self.location_repo.create(data)

        # Update related hotel's location count
        self.hotel_repo.increment_location_count(data.hotel_id)

        # Single commit for both operations (atomic transaction)
        self.session.commit()
        self.session.refresh(location)
        return location
```

### Routes

Routes stay thin and delegate to services or repositories:

```python
# app/routes/location.py
from fastapi import APIRouter, Depends
from sqlmodel import Session
from database import get_session
from app.schemas.location_schema import LocationCreate, LocationRead
from app.services.location_service import LocationService

router = APIRouter(prefix="/locations", tags=["locations"])

@router.post("/", response_model=LocationRead)
def create_location(data: LocationCreate, session: Session = Depends(get_session)):
    service = LocationService(session)
    return service.create(data)
```

## When to Use Each

| Scenario | Use |
|----------|-----|
| Simple CRUD on one table | Repository directly in route |
| Operation affects multiple tables | Service coordinating repositories |
| Complex business logic | Service |
| Reusable DB queries | Repository |

## Directory Structure

```
app/
  models/          # SQLModel entities (table=True)
  schemas/         # Pydantic models for request/response validation
  repositories/    # Single-table database operations
  services/        # Business logic coordinating repositories
  routes/          # FastAPI endpoints
```
