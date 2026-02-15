"""Storage service protocol."""

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
