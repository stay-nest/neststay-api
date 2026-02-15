# Plan: Include Images in Location API Responses

## Context
The `LocationImage` system is fully implemented (model, repo, service, routes), but the location listing and detail endpoints don't include image data in their responses. The goal is to:
- **Listing** (`GET /locations/`, `GET /locations/hotel/{hotel_id}`) — include only the **featured image**
- **Detail** (`GET /locations/{slug}`) — include **all images**

## Approach: Model Relationship + Separate Schemas (no N+1)

Use a **filtered SQLAlchemy relationship** on the Location model for `featured_image` with `lazy="selectin"` — SQLAlchemy automatically batch-loads in a single `WHERE location_id IN (...)` query. For the detail page, explicitly eager-load the full `images` relationship.

Since `LocationImageRead` has a computed `url` field (via `storage.get_url()`), the relationship handles SQL loading and the service handles URL computation.

---

## Files to Modify

### 1. `app/models/location.py` — Add filtered relationship
Add a `featured_image` relationship with a filtered `primaryjoin` and `lazy="selectin"`:
```python
featured_image: "LocationImage" | None = Relationship(
    sa_relationship_kwargs={
        "primaryjoin": "and_(Location.id == foreign(LocationImage.location_id), LocationImage.is_featured == True)",
        "uselist": False,
        "viewonly": True,
        "lazy": "selectin",
    }
)
```
- `lazy="selectin"` — auto batch-loads via `SELECT ... WHERE location_id IN (...)`
- `viewonly=True` — read-only, won't interfere with the existing `images` relationship
- `uselist=False` — returns single object, not a list

### 2. `app/schemas/location_schema.py` — Add image fields to responses
```python
from app.schemas.location_image_schema import LocationImageRead

class LocationRead(BaseModel):
    # ... existing fields ...
    featured_image: LocationImageRead | None = None  # NEW

class LocationDetailRead(LocationRead):
    """Detail response with all images."""
    images: list[LocationImageRead] = []  # NEW
```

### 3. `app/services/location_service.py` — Build responses with image URLs
- Inject `StorageService` (from `get_storage_service()`)
- Add `_image_to_read(img: LocationImage) -> LocationImageRead` helper (same pattern as `LocationImageService._model_to_read`)
- Add `_location_to_read(location: Location) -> LocationRead` helper that converts the model including `featured_image`
- **`list_locations()`** / **`list_by_hotel()`**: use `_location_to_read()` instead of `LocationRead.model_validate()` — the `featured_image` relationship is already loaded by `selectin`
- **`get_by_slug()`**: return `LocationDetailRead` with all images — needs explicit image loading (see repo change below)

### 4. `app/repositories/location_repo.py` — Eager-load images for detail
Update `get_by_slug()` to also eager-load the `images` relationship:
```python
from sqlalchemy.orm import defer, selectinload

def get_by_slug(self, slug: str) -> Location | None:
    statement = (
        select(Location)
        .options(
            defer(Location.contact_email),
            defer(Location.contact_phone),
            selectinload(Location.images),  # NEW — load all images for detail
        )
        .where(Location.slug == slug)
        .where(Location.is_active)
    )
    return self.session.exec(statement).first()
```

### 5. `app/routes/location.py` — Update detail response type
- Import `LocationDetailRead`
- Change `get_location` endpoint response_model to `LocationDetailRead`
- Update the handler to call a service method that returns `LocationDetailRead`

---

## Query Summary (no N+1)
| Endpoint | Queries | How |
|----------|---------|-----|
| `GET /locations/` | 2 + count | locations query + auto `selectin` for featured_image |
| `GET /locations/hotel/{id}` | 2 + count | same pattern |
| `GET /locations/{slug}` | 2 | location + `selectinload` for all images |

---

## Key Reusable Code
- `LocationImageService._model_to_read()` at `app/services/location_image_service.py:68` — pattern for building `LocationImageRead` with URL
- `get_storage_service()` at `app/services/storage/__init__.py` — factory for storage service
- `StorageService.get_url(path)` — computes public URL from file path

## Verification
1. `make test` — all existing tests must pass
2. Test listing: `GET /locations/` — each location has `featured_image` (null if none set)
3. Test detail: `GET /locations/{slug}` — has `images` array with all images + `featured_image`
4. Test listing by hotel: `GET /locations/hotel/{hotel_id}` — same as listing
