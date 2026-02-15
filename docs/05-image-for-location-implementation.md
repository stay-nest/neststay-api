# Location Images Implementation Plan

## Overview
Add multiple image upload support for locations with a featured image capability.

## Design Decisions

### 1. Dedicated `LocationImage` Model
- Create a separate `LocationImage` model with foreign key to `Location`
- Follows the existing pattern of domain-specific models (Hotel, Location, RoomType)
- Simpler than a generic polymorphic Image model

### 2. Storage Abstraction Layer (Strategy Pattern)
- Create a `StorageService` protocol/interface with pluggable implementations
- Start with `LocalStorageService`, easily add `S3StorageService` later
- `LocationImageService` depends on the abstraction, not a concrete implementation
- Config setting `STORAGE_TYPE` controls which implementation is used

### 3. Featured Image: Boolean Flag
- Use `is_featured: bool` on `LocationImage` (not a foreign key on Location)
- Service layer ensures only one featured image per location
- Avoids circular dependency and nullable FK complexity

---

## Storage Abstraction Architecture

### Protocol Definition (`app/services/storage/base.py`)
```python
from typing import Protocol

class StorageService(Protocol):
    """Abstract interface for file storage."""

    def save(self, file_content: bytes, filename: str, path: str) -> str:
        """Save file and return the stored path/URL."""
        ...

    def delete(self, path: str) -> None:
        """Delete a file from storage."""
        ...

    def get_url(self, path: str) -> str:
        """Get public URL for a stored file."""
        ...
```

### Implementations

**LocalStorageService** (`app/services/storage/local.py`)
- Saves to `{UPLOAD_DIR}/locations/{location_id}/{uuid}.{ext}`
- Returns relative path; served via FastAPI StaticFiles
- `get_url()` returns `/uploads/{path}`

**S3StorageService** (`app/services/storage/s3.py`) - Future
- Uses boto3 to upload to S3 bucket
- Returns S3 URL or CloudFront URL
- Config: `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `S3_BUCKET`, `S3_REGION`

### Factory Function (`app/services/storage/__init__.py`)
```python
def get_storage_service() -> StorageService:
    if settings.STORAGE_TYPE == "s3":
        return S3StorageService(...)
    return LocalStorageService(settings.UPLOAD_DIR)
```

### Config Settings
```python
STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")  # "local" | "s3"
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")

# Future S3 settings (only needed when STORAGE_TYPE="s3")
# AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET, S3_REGION, CLOUDFRONT_URL
```

---

## Files to Create

### 1. `app/models/location_image.py`
```python
class LocationImage(SQLModel, table=True):
    id: int | None
    location_id: int  # FK to locations.id
    filename: str     # Original filename
    file_path: str    # Relative path (e.g., "locations/1/uuid.jpg")
    alt_text: str | None
    is_featured: bool = False
    sort_order: int = 0
    created_at: datetime
```

### 2. `app/repositories/location_image_repo.py`
Methods: `create`, `get_by_id`, `get_by_location`, `get_featured_by_location`, `unset_featured_for_location`, `delete`, `update`

### 3. `app/services/storage/` (Storage Abstraction)
- `base.py` - `StorageService` protocol
- `local.py` - `LocalStorageService` implementation
- `__init__.py` - Factory function `get_storage_service()`

### 4. `app/services/location_image_service.py`
- Inject `StorageService` via constructor (or use factory)
- Validate file type (jpg, jpeg, png, gif, webp) and size (5MB limit)
- Delegate file operations to `StorageService`
- Manage featured image (unset previous when setting new)

### 5. `app/schemas/location_image_schema.py`
- `LocationImageCreate` - alt_text (optional)
- `LocationImageUpdate` - alt_text, sort_order
- `LocationImageRead` - full response with all fields

### 6. `app/routes/location_image.py`
Nested under `/locations/{location_id}/images`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Upload image (multipart form) |
| GET | `/` | List all images |
| POST | `/{image_id}/featured` | Set as featured |
| PATCH | `/{image_id}` | Update alt_text/sort_order |
| DELETE | `/{image_id}` | Delete image |

---

## Files to Modify

### 1. `app/models/location.py`
Add relationship:
```python
images: list["LocationImage"] = Relationship(back_populates="location")
```

### 2. `app/models/__init__.py`
Add `LocationImage` to imports and `__all__`

### 3. `config.py`
Add:
```python
STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")  # "local" | "s3"
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
```

### 4. `main.py`
- Import and register `location_image` router
- Mount static files: `app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")`

### 5. `database/alembic/env.py`
Add `LocationImage` to model imports

### 6. `tests/conftest.py`
Add `LocationImage` import for table creation

---

## Implementation Sequence

1. **Model & Migration**
   - Create `LocationImage` model
   - Update `Location` model with images relationship
   - Update imports (`models/__init__.py`, `alembic/env.py`)
   - Run `make migrate-make MESSAGE="create location_images table"`
   - Run `make migrate`

2. **Repository** - Create `LocationImageRepository`

3. **Config** - Add `STORAGE_TYPE` and `UPLOAD_DIR` settings

4. **Storage Abstraction**
   - Create `app/services/storage/base.py` with `StorageService` protocol
   - Create `app/services/storage/local.py` with `LocalStorageService`
   - Create `app/services/storage/__init__.py` with factory function

5. **Service** - Create `LocationImageService` using `StorageService`

6. **Schemas** - Create request/response schemas

7. **Routes** - Create endpoints and register in `main.py`

8. **Static Files** - Mount uploads directory (for local storage)

9. **Tests** - Add tests for the new functionality

---

## Verification

1. Run `make migrate` to apply migrations
2. Test image upload: `curl -X POST -F "file=@test.jpg" http://localhost:8000/locations/{id}/images/`
3. Test list images: `GET /locations/{id}/images/`
4. Test set featured: `POST /locations/{id}/images/{img_id}/featured`
5. Test delete: `DELETE /locations/{id}/images/{img_id}`
6. Verify file appears in `uploads/locations/{id}/`
7. Run `make test` to ensure all tests pass
