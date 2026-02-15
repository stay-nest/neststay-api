"""Storage service factory and types."""

from app.services.storage.base import StorageService
from app.services.storage.local import LocalStorageService


def get_storage_service(settings: object) -> StorageService:
    """
    Return the configured storage implementation.

    Args:
        settings: Application settings with STORAGE_TYPE and UPLOAD_DIR

    Returns:
        StorageService implementation (LocalStorageService when STORAGE_TYPE is "local")
    """
    storage_type = getattr(settings, "STORAGE_TYPE", "local")
    upload_dir = getattr(settings, "UPLOAD_DIR", "uploads")
    if storage_type == "s3":
        raise NotImplementedError("S3 storage not implemented yet")
    return LocalStorageService(upload_dir)
