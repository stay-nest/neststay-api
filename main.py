"""FastAPI application entry point."""

from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from app.routes import (
    admin_guest as admin_guest_routes,
    admin_room_type as admin_room_type_routes,
    auth as auth_routes,
    guest as guest_routes,
    hotel as hotel_routes,
    location as location_routes,
    location_image as location_image_routes,
)
from config import settings
from database import get_session

app = FastAPI(
    title="NestStay API", description="API for NestStay application", version="0.1.0"
)

# Ensure upload directory exists and mount static files for local storage
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Register routers
app.include_router(auth_routes.router)
app.include_router(guest_routes.router)
app.include_router(admin_guest_routes.router)
app.include_router(admin_room_type_routes.router)
app.include_router(hotel_routes.router)
app.include_router(location_routes.router)
app.include_router(location_image_routes.router, prefix="/locations")


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to NestStay API"}


@app.get("/health")
def health_check(session: Session = Depends(get_session)):
    """Health check endpoint."""
    return {"status": "healthy", "database": "connected"}
