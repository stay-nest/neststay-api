"""Location image routes."""

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlmodel import Session

from app.dependencies.auth import get_current_guest
from app.models.guest import Guest
from app.schemas.location_image_schema import (
    LocationImageRead,
    LocationImageUpdate,
)
from app.services.location_image_service import LocationImageService
from app.services.storage import get_storage_service
from config import settings
from database import get_session

router = APIRouter(prefix="/{location_id}/images", tags=["location-images"])


def get_storage():
    """Dependency that returns the configured storage service."""
    return get_storage_service(settings)


@router.post("/", response_model=LocationImageRead, status_code=status.HTTP_201_CREATED)
def upload_image(
    location_id: int,
    file: UploadFile = File(...),
    alt_text: str | None = Form(None),
    is_featured: str | None = Form(None),
    session: Session = Depends(get_session),
    storage=Depends(get_storage),
    current_guest: Guest = Depends(get_current_guest),
) -> LocationImageRead:
    """Upload an image for a location."""
    featured = is_featured is not None and str(is_featured).lower() in (
        "true",
        "1",
        "yes",
    )
    service = LocationImageService(session, storage)
    return service.upload(
        location_id,
        file,
        alt_text=alt_text,
        is_featured=featured,
    )


@router.get("/", response_model=list[LocationImageRead])
def list_images(
    location_id: int,
    session: Session = Depends(get_session),
    storage=Depends(get_storage),
    current_guest: Guest = Depends(get_current_guest),
) -> list[LocationImageRead]:
    """List all images for a location."""
    service = LocationImageService(session, storage)
    return service.list_images(location_id)


@router.post("/{image_id}/featured", response_model=LocationImageRead)
def set_featured_image(
    location_id: int,
    image_id: int,
    session: Session = Depends(get_session),
    storage=Depends(get_storage),
    current_guest: Guest = Depends(get_current_guest),
) -> LocationImageRead:
    """Set an image as the featured image for the location."""
    service = LocationImageService(session, storage)
    return service.set_featured(location_id, image_id)


@router.patch("/{image_id}", response_model=LocationImageRead)
def update_image(
    location_id: int,
    image_id: int,
    data: LocationImageUpdate,
    session: Session = Depends(get_session),
    storage=Depends(get_storage),
    current_guest: Guest = Depends(get_current_guest),
) -> LocationImageRead:
    """Update alt_text or sort_order for an image."""
    service = LocationImageService(session, storage)
    return service.update(location_id, image_id, data)


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    location_id: int,
    image_id: int,
    session: Session = Depends(get_session),
    storage=Depends(get_storage),
    current_guest: Guest = Depends(get_current_guest),
) -> None:
    """Delete an image and its file from storage."""
    service = LocationImageService(session, storage)
    service.delete(location_id, image_id)
