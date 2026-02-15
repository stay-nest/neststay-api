"""LocationImage repository for single-table database operations."""

from sqlmodel import Session, select

from app.models.location_image import LocationImage


class LocationImageRepository:
    """Repository for LocationImage entity operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create(self, location_image: LocationImage) -> LocationImage:
        """
        Create a location image instance.

        Args:
            location_image: LocationImage instance to create

        Returns:
            Created location image instance (not yet committed)
        """
        self.session.add(location_image)
        return location_image

    def get_by_id(self, image_id: int) -> LocationImage | None:
        """
        Get location image by ID.

        Args:
            image_id: The image ID to look up

        Returns:
            LocationImage instance if found, None otherwise
        """
        statement = select(LocationImage).where(LocationImage.id == image_id)
        return self.session.exec(statement).first()

    def get_by_location(self, location_id: int) -> list[LocationImage]:
        """
        Get all images for a location, ordered by sort_order then id.

        Args:
            location_id: The location ID to filter by

        Returns:
            List of LocationImage instances
        """
        statement = (
            select(LocationImage)
            .where(LocationImage.location_id == location_id)
            .order_by(LocationImage.sort_order, LocationImage.id)  # type: ignore[arg-type]
        )
        return list(self.session.exec(statement).all())

    def get_featured_by_location(self, location_id: int) -> LocationImage | None:
        """
        Get the featured image for a location, if any.

        Args:
            location_id: The location ID to filter by

        Returns:
            Featured LocationImage or None
        """
        statement = (
            select(LocationImage)
            .where(LocationImage.location_id == location_id)
            .where(LocationImage.is_featured)
        )
        return self.session.exec(statement).first()

    def unset_featured_for_location(self, location_id: int) -> None:
        """
        Set is_featured=False for all images of the given location.

        Args:
            location_id: The location ID
        """
        images = self.get_by_location(location_id)
        for img in images:
            if img.is_featured:
                img.is_featured = False
                self.session.add(img)

    def update(self, location_image: LocationImage) -> LocationImage:
        """
        Update a location image instance.

        Args:
            location_image: LocationImage instance to update

        Returns:
            Updated location image instance (not yet committed)
        """
        self.session.add(location_image)
        return location_image

    def delete(self, location_image: LocationImage) -> None:
        """
        Delete a location image from the database.

        Args:
            location_image: LocationImage instance to delete
        """
        self.session.delete(location_image)
