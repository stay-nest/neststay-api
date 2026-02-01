# Guest Management API Implementation Plan

## Overview

Implement guest management routes for both public (guest self-service) and admin operations. The model, repository, service, and schemas already exist - only routes need to be created.

## Existing Components

| Layer | File | Status |
|-------|------|--------|
| Model | `app/models/guest.py` | ✅ Complete |
| Schemas | `app/schemas/guest_schema.py` | ✅ Complete |
| Repository | `app/repositories/guest_repo.py` | ✅ Complete |
| Service | `app/services/guest_service.py` | ✅ Complete |
| Routes | - | ❌ Needs creation |

## API Endpoints to Implement

### Public Guest Routes (`/guest`)

| Method | Endpoint | Service Method | Description |
|--------|----------|----------------|-------------|
| POST | `/guest/register` | `register_guest_by_phone_number` or `register_guest_by_email` | Register new guest |
| GET | `/guest/by-phone/{phone_number}` | `get_guest_by_phone_number` | Lookup by phone |
| GET | `/guest/by-email/{email}` | `get_guest_by_email` | Lookup by email |
| GET | `/guest/{guest_id}` | `get_guest_by_id` | Lookup by ID |
| PUT | `/guest/{guest_id}` | `update_guest` | Update guest |
| DELETE | `/guest/{guest_id}` | `delete_guest` | Delete guest (soft delete) |

### Admin Routes (`/admin/guest`)

| Method | Endpoint | Service Method | Description |
|--------|----------|----------------|-------------|
| GET | `/admin/guest/` | `get_all_guests` | List all guests (paginated) |
| DELETE | `/admin/guest/{guest_id}` | `delete_guest` | Delete a guest (soft delete) |

## Implementation Steps

### 1. Create Registration Schema

**File:** `app/schemas/guest_schema.py` (add to existing)

Add a unified registration schema that handles both flows:

```python
class GuestRegister(BaseModel):
    """Guest registration - phone OR email+password flow."""
    name: str
    phone_number: str | None = None
    email: str | None = None
    password: str | None = None

    # Validation: must provide phone_number OR (email + password)
```

The service will determine the registration flow:
- If `phone_number` is provided → phone registration flow
- If `email` and `password` are provided → email registration flow
- Missing required fields → 400 Bad Request

### 2. Create Public Guest Routes

**File:** `app/routes/guest.py` (new file)

```python
router = APIRouter(prefix="/guest", tags=["guest"])

# POST /guest/register - conditionally routes to phone or email registration
# GET /guest/by-phone/{phone_number}
# GET /guest/by-email/{email}
# GET /guest/{guest_id}
# PUT /guest/{guest_id}
# DELETE /guest/{guest_id}
```

### 3. Create Admin Guest Routes

**File:** `app/routes/admin_guest.py` (new file)

```python
router = APIRouter(prefix="/admin/guest", tags=["admin-guest"])

# GET /admin/guest/ - list all guests with pagination
# DELETE /admin/guest/{guest_id} - soft delete guest
```

### 4. Register Routes in Main

**File:** `main.py`

Add imports and router registration:
```python
from app.routes import guest as guest_routes
from app.routes import admin_guest as admin_guest_routes

app.include_router(guest_routes.router)
app.include_router(admin_guest_routes.router)
```

### 5. Create Tests

**File:** `tests/api/test_guests.py` (new file)

Test coverage for:
- Guest registration (phone flow)
- Guest registration (email flow)
- Duplicate registration handling (409)
- Get guest by phone/email/id
- Update guest
- Delete guest
- Admin list guests
- Admin delete guest

## Files to Create/Modify

| File | Action |
|------|--------|
| `app/schemas/guest_schema.py` | Add registration schema |
| `app/routes/guest.py` | Create (public guest routes) |
| `app/routes/admin_guest.py` | Create (admin guest routes) |
| `main.py` | Add route imports and registration |
| `tests/api/test_guests.py` | Create (test suite) |

## Verification

1. Run `make test` to ensure all existing tests still pass
2. Test each endpoint manually or via new tests:
   - Register a guest by phone
   - Register a guest by email
   - Attempt duplicate registration (expect 409)
   - Lookup by phone/email/id
   - Update a guest
   - Delete a guest
   - Admin list all guests
   - Admin delete a guest
