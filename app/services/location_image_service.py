"""Location image service for upload, list, featured, update, delete."""

import uuid

from fastapi import HTTPException, UploadFile, status
from sqlmodel import Session

from app.models.location_image import LocationImage
from app.repositories.location_image_repo import LocationImageRepository
from app.repositories.location_repo import LocationRepository
from app.schemas.location_image_schema import LocationImageRead, LocationImageUpdate
from app.services.storage.base import StorageService

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "avif"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


class LocationImageService:
    """Service for location image business logic."""

    def __init__(self, session: Session, storage: StorageService):
        """Initialize with session and storage backend."""
        self.session = session
        self.storage = storage
        self.location_repo = LocationRepository(session)
        self.image_repo = LocationImageRepository(session)

    def _get_location_or_404(self, location_id: int):
        """Return location or raise 404."""
        location = self.location_repo.get_by_id(location_id)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location with id '{location_id}' not found",
            )
        return location

    def _get_image_for_location_or_404(
        self, location_id: int, image_id: int
    ) -> LocationImage:
        """Return image belonging to location or raise 404."""
        image = self.image_repo.get_by_id(image_id)
        if not image or image.location_id != location_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found",
            )
        return image

    def _validate_file(self, file: UploadFile) -> tuple[bytes, str]:
        """Validate file type and size; return (content, extension)."""
        content = file.file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            limit_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds {limit_mb}MB limit",
            )
        filename = file.filename or "image"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
            )
        return content, ext

    def _model_to_read(self, img: LocationImage) -> LocationImageRead:
        """Build LocationImageRead with url from storage."""
        return LocationImageRead(
            id=img.id,
            location_id=img.location_id,
            filename=img.filename,
            file_path=img.file_path,
            url=self.storage.get_url(img.file_path),
            alt_text=img.alt_text,
            is_featured=img.is_featured,
            sort_order=img.sort_order,
            created_at=img.created_at,
        )

    def upload(
        self,
        location_id: int,
        file: UploadFile,
        alt_text: str | None = None,
        is_featured: bool = False,
    ) -> LocationImageRead:
        """
        Upload an image for a location.

        Validates location exists, file type/size, saves via storage, creates DB record.
        If is_featured is True, unsets previous featured and sets this one.
        """
        self._get_location_or_404(location_id)
        content, ext = self._validate_file(file)
        original_filename = file.filename or "image"

        path = f"locations/{location_id}/{uuid.uuid4().hex}.{ext}"
        stored_path = self.storage.save(content, original_filename, path)

        existing = self.image_repo.get_by_location(location_id)
        sort_order = max((img.sort_order for img in existing), default=-1) + 1

        image = LocationImage(
            location_id=location_id,
            filename=original_filename,
            file_path=stored_path,
            alt_text=alt_text,
            is_featured=is_featured,
            sort_order=sort_order,
        )
        if is_featured:
            self.image_repo.unset_featured_for_location(location_id)
            image.is_featured = True
        self.image_repo.create(image)
        self.session.commit()
        self.session.refresh(image)
        return self._model_to_read(image)

    def list_images(self, location_id: int) -> list[LocationImageRead]:
        """List all images for a location with urls."""
        self._get_location_or_404(location_id)
        images = self.image_repo.get_by_location(location_id)
        return [self._model_to_read(img) for img in images]

    def set_featured(self, location_id: int, image_id: int) -> LocationImageRead:
        """Set the given image as the featured image for the location."""
        image = self._get_image_for_location_or_404(location_id, image_id)
        self.image_repo.unset_featured_for_location(location_id)
        image.is_featured = True
        self.image_repo.update(image)
        self.session.commit()
        self.session.refresh(image)
        return self._model_to_read(image)

    def update(
        self,
        location_id: int,
        image_id: int,
        data: LocationImageUpdate,
    ) -> LocationImageRead:
        """Update alt_text and/or sort_order for an image."""
        image = self._get_image_for_location_or_404(location_id, image_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(image, field, value)
        self.image_repo.update(image)
        self.session.commit()
        self.session.refresh(image)
        return self._model_to_read(image)

    def delete(self, location_id: int, image_id: int) -> None:
        """Delete image and remove file from storage."""
        image = self._get_image_for_location_or_404(location_id, image_id)
        self.storage.delete(image.file_path)
        self.image_repo.delete(image)
        self.session.commit()
