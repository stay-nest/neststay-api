"""FastAPI application entry point."""

from fastapi import Depends, FastAPI
from sqlmodel import Session

from app.routes import (
    admin_guest as admin_guest_routes,
    guest as guest_routes,
    hotel as hotel_routes,
    location as location_routes,
)
from database import get_session

app = FastAPI(
    title="NestStay API", description="API for NestStay application", version="0.1.0"
)

# Register routers
app.include_router(guest_routes.router)
app.include_router(admin_guest_routes.router)
app.include_router(hotel_routes.router)
app.include_router(location_routes.router)


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to NestStay API"}


@app.get("/health")
def health_check(session: Session = Depends(get_session)):
    """Health check endpoint."""
    return {"status": "healthy", "database": "connected"}
