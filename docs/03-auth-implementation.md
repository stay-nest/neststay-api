# JWT Authentication Implementation Plan

## Overview

Implement JWT-based authentication with bearer tokens for the FastAPI backend. Uses stateless JWTs for both access and refresh tokens with "refresh on 401" pattern for the Next.js frontend.

## Token Configuration

| Token | Expiry | Purpose |
|-------|--------|---------|
| Access Token | 15 minutes | API authorization via `Authorization: Bearer <token>` |
| Refresh Token | 7 days | Get new access tokens via `/auth/refresh` |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login with email+password, returns access + refresh tokens |
| POST | `/auth/refresh` | Exchange refresh token for new access token |
| POST | `/auth/logout` | Client-side only (discard tokens) |
| GET | `/auth/me` | Get current authenticated user |

## Implementation Steps

### 1. Install Dependencies

```bash
uv add python-jose[cryptography]
```

### 2. Add JWT Settings to Config

**File:** `config.py`

```python
# JWT settings
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
REFRESH_TOKEN_EXPIRE_DAYS: int = 7
```

### 3. Create Auth Utilities

**File:** `app/utils/jwt.py` (new)

```python
def create_access_token(subject: int) -> str:
    """Create short-lived access token with guest_id as subject."""

def create_refresh_token(subject: int) -> str:
    """Create long-lived refresh token with guest_id as subject."""

def decode_token(token: str) -> dict:
    """Decode and validate JWT. Raises JWTError if invalid/expired."""
```

### 4. Add Password Verification

**File:** `app/utils/password.py` (add to existing)

```python
def verify_password(plain: str, hashed: str) -> bool:
    """Verify plain password against hashed password."""
```

### 5. Create Auth Schemas

**File:** `app/schemas/auth_schema.py` (new)

```python
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str
```

### 6. Create Auth Service

**File:** `app/services/auth_service.py` (new)

```python
class AuthService:
    def authenticate(self, email: str, password: str) -> Guest:
        """Validate credentials, return guest or raise 401."""

    def create_tokens(self, guest_id: int) -> TokenResponse:
        """Generate access + refresh token pair."""

    def refresh_access_token(self, refresh_token: str) -> str:
        """Validate refresh token, return new access token."""
```

### 7. Create Auth Dependency

**File:** `app/dependencies/auth.py` (new)

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_guest(token: str = Depends(oauth2_scheme)) -> Guest:
    """Dependency to extract guest from JWT. Raises 401 if invalid."""
```

### 8. Create Auth Routes

**File:** `app/routes/auth.py` (new)

```python
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, session: Session = Depends(get_session)):
    """Authenticate and return tokens."""

@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, session: Session = Depends(get_session)):
    """Exchange refresh token for new access token."""

@router.get("/me", response_model=GuestRead)
def get_me(current_guest: Guest = Depends(get_current_guest)):
    """Get current authenticated guest."""
```

### 9. Register Routes

**File:** `main.py`

```python
from app.routes import auth as auth_routes
app.include_router(auth_routes.router)
```

### 10. Create Tests

**File:** `tests/api/test_auth.py` (new)

Test coverage:
- Login with valid credentials
- Login with invalid email (401)
- Login with invalid password (401)
- Refresh with valid token
- Refresh with expired token (401)
- Refresh with invalid token (401)
- Access protected route with valid token
- Access protected route without token (401)
- Access protected route with expired token (401)

## Files to Create/Modify

| File | Action |
|------|--------|
| `pyproject.toml` | Add python-jose dependency |
| `config.py` | Add JWT settings |
| `app/utils/jwt.py` | Create (JWT utilities) |
| `app/utils/password.py` | Add verify_password function |
| `app/schemas/auth_schema.py` | Create (auth schemas) |
| `app/services/auth_service.py` | Create (auth service) |
| `app/dependencies/auth.py` | Create (auth dependency) |
| `app/routes/auth.py` | Create (auth routes) |
| `main.py` | Register auth router |
| `tests/api/test_auth.py` | Create (test suite) |

## Environment Variables

Add to `.env`:

```
JWT_SECRET_KEY=your-secure-random-key-here
```

Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Usage in Protected Routes

To protect any route, add the `get_current_guest` dependency:

```python
from app.dependencies.auth import get_current_guest

@router.get("/protected")
def protected_route(current_guest: Guest = Depends(get_current_guest)):
    return {"message": f"Hello {current_guest.name}"}
```

## Frontend Integration (Next.js)

The frontend should:
1. Store access token in memory (React state/context)
2. Store refresh token in httpOnly cookie or secure storage
3. Add Axios interceptor to handle 401 → refresh → retry pattern
4. Attach `Authorization: Bearer <access_token>` to all API requests

## Verification

1. Run `make test` to ensure all tests pass
2. Manual testing:
   - Register a guest (from guest APIs)
   - Login with email/password → get tokens
   - Access `/auth/me` with access token
   - Wait 15+ min or use expired token → get 401
   - Call `/auth/refresh` → get new access token
   - Access `/auth/me` with new token → success
