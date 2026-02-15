"""Unit tests for location schemas (LocationRead, LocationDetailRead, featured_image, images)."""

from app.schemas.location_image_schema import LocationImageReadEmbedded
from app.schemas.location_schema import LocationDetailRead, LocationRead


class TestLocationRead:
    """LocationRead schema: fields and featured_image embedding."""

    def test_has_featured_image_field(self) -> None:
        assert "featured_image" in LocationRead.model_fields
        assert LocationRead.model_fields["featured_image"].annotation == (
            LocationImageReadEmbedded | None
        )

    def test_featured_image_default_none(self) -> None:
        data = {
            "slug": "test-location",
            "hotel_id": 1,
            "name": "Test",
            "address": "123 St",
            "city": "City",
            "state": "ST",
            "country": "Country",
            "is_active": True,
        }
        loc = LocationRead(**data)
        assert loc.featured_image is None

    def test_featured_image_accepts_embedded_image_without_id(self) -> None:
        data = {
            "slug": "test-location",
            "hotel_id": 1,
            "name": "Test",
            "address": "123 St",
            "city": "City",
            "state": "ST",
            "country": "Country",
            "is_active": True,
            "featured_image": {
                "filename": "photo.jpg",
                "file_path": "locations/1/photo.jpg",
                "url": "/uploads/locations/1/photo.jpg",
                "alt_text": "A photo",
                "is_featured": True,
                "sort_order": 0,
                "created_at": "2025-01-01T00:00:00",
            },
        }
        loc = LocationRead(**data)
        assert loc.featured_image is not None
        assert loc.featured_image.filename == "photo.jpg"
        assert loc.featured_image.url == "/uploads/locations/1/photo.jpg"
        assert not hasattr(loc.featured_image, "id") or getattr(
            loc.featured_image, "id", None
        ) is None
        assert "id" not in loc.featured_image.model_dump()
        assert "location_id" not in loc.featured_image.model_dump()


class TestLocationDetailRead:
    """LocationDetailRead extends LocationRead with images list."""

    def test_inherits_from_location_read(self) -> None:
        assert issubclass(LocationDetailRead, LocationRead)

    def test_has_images_field(self) -> None:
        assert "images" in LocationDetailRead.model_fields
        assert LocationDetailRead.model_fields["images"].annotation == list[
            LocationImageReadEmbedded
        ]

    def test_images_default_empty_list(self) -> None:
        data = {
            "slug": "test-location",
            "hotel_id": 1,
            "name": "Test",
            "address": "123 St",
            "city": "City",
            "state": "ST",
            "country": "Country",
            "is_active": True,
        }
        detail = LocationDetailRead(**data)
        assert detail.images == []

    def test_images_accepts_embedded_items_without_id(self) -> None:
        data = {
            "slug": "test-location",
            "hotel_id": 1,
            "name": "Test",
            "address": "123 St",
            "city": "City",
            "state": "ST",
            "country": "Country",
            "is_active": True,
            "images": [
                {
                    "filename": "a.jpg",
                    "file_path": "locations/1/a.jpg",
                    "url": "/uploads/locations/1/a.jpg",
                    "alt_text": None,
                    "is_featured": True,
                    "sort_order": 0,
                    "created_at": "2025-01-01T00:00:00",
                },
            ],
        }
        detail = LocationDetailRead(**data)
        assert len(detail.images) == 1
        assert detail.images[0].filename == "a.jpg"
        assert "id" not in detail.images[0].model_dump()
        assert "location_id" not in detail.images[0].model_dump()
