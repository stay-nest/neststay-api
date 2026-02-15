"""Tests for location list and detail API (featured_image and images in response)."""

import tempfile

import pytest
from fastapi.testclient import TestClient

from app.routes.location import get_storage as get_location_storage
from app.routes.location_image import get_storage as get_location_image_storage
from app.services.storage.local import LocalStorageService

# Minimal valid JPEG (1x1 pixel)
MINIMAL_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n"
    b"\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d"
    b"\x1a\x1c\x1c $.' \",#\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c"
    b"\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c"
    b"\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\xff\xc0\x00\x0b\x08\x00"
    b"\x01\x00\x01\x01\x01\x00\x1f\x00\xff\xc4\x00\x1f\x00\x00\x01\x05"
    b"\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02"
    b"\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x0c\x03\x01\x00\x02"
    b"\x10\x03\x10\x00\x00\x01\x1f\x00\xff\xd9"
)


@pytest.fixture
def temp_upload_dir_and_storage_overrides():
    """Override both location and location_image storage to same temp dir."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageService(tmpdir)
        from main import app

        app.dependency_overrides[get_location_storage] = lambda: storage
        app.dependency_overrides[get_location_image_storage] = lambda: storage
        yield tmpdir
        app.dependency_overrides.pop(get_location_storage, None)
        app.dependency_overrides.pop(get_location_image_storage, None)


class TestListLocationsWithFeaturedImage:
    """GET /locations/ and GET /locations/hotel/{id} include featured_image."""

    def test_list_locations_each_item_has_featured_image_key(
        self,
        client: TestClient,
        db_hotel_and_location: dict,
        temp_upload_dir_and_storage_overrides: str,
    ) -> None:
        """Every location in list response has featured_image (null or object)."""
        response = client.get("/locations/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        for item in data["items"]:
            assert "featured_image" in item
            if item["featured_image"] is not None:
                # Embedded image must not expose id or location_id
                assert "id" not in item["featured_image"]
                assert "location_id" not in item["featured_image"]

    def test_list_by_hotel_each_item_has_featured_image_key(
        self,
        client: TestClient,
        db_hotel_and_location: dict,
        temp_upload_dir_and_storage_overrides: str,
    ) -> None:
        """Locations by hotel have featured_image key."""
        hotel_id = db_hotel_and_location["hotel"].id
        response = client.get(f"/locations/hotel/{hotel_id}")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert "featured_image" in item

    def test_list_featured_image_embedded_has_no_id_when_present(
        self,
        client: TestClient,
        db_hotel_and_location: dict,
        temp_upload_dir_and_storage_overrides: str,
        auth_headers: dict,
    ) -> None:
        """When a location has a featured image, embedded object has no id/location_id."""
        location_id = db_hotel_and_location["location"].id
        slug = db_hotel_and_location["location"].slug
        # Upload and set as featured
        client.post(
            f"/locations/{location_id}/images/",
            files={"file": ("featured.jpg", MINIMAL_JPEG, "image/jpeg")},
            data={"is_featured": "true"},
            headers=auth_headers,
        )
        response = client.get("/locations/")
        assert response.status_code == 200
        items = response.json()["items"]
        loc = next((i for i in items if i["slug"] == slug), None)
        assert loc is not None
        assert loc["featured_image"] is not None
        assert "id" not in loc["featured_image"]
        assert "location_id" not in loc["featured_image"]
        assert "url" in loc["featured_image"]
        assert "filename" in loc["featured_image"]


class TestGetLocationDetailWithImages:
    """GET /locations/{slug} returns LocationDetailRead with images array."""

    def test_detail_response_has_images_key(
        self,
        client: TestClient,
        db_hotel_and_location: dict,
        temp_upload_dir_and_storage_overrides: str,
    ) -> None:
        """Detail response includes images array."""
        slug = db_hotel_and_location["location"].slug
        response = client.get(f"/locations/{slug}")
        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        assert isinstance(data["images"], list)

    def test_detail_embedded_images_have_no_id(
        self,
        client: TestClient,
        db_hotel_and_location: dict,
        temp_upload_dir_and_storage_overrides: str,
        auth_headers: dict,
    ) -> None:
        """Each image in detail.images does not expose id or location_id."""
        location_id = db_hotel_and_location["location"].id
        slug = db_hotel_and_location["location"].slug
        client.post(
            f"/locations/{location_id}/images/",
            files={"file": ("photo.jpg", MINIMAL_JPEG, "image/jpeg")},
            headers=auth_headers,
        )
        response = client.get(f"/locations/{slug}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["images"]) >= 1
        for img in data["images"]:
            assert "id" not in img
            assert "location_id" not in img
            assert "url" in img
            assert "filename" in img

    def test_detail_also_has_featured_image_key(
        self,
        client: TestClient,
        db_hotel_and_location: dict,
        temp_upload_dir_and_storage_overrides: str,
    ) -> None:
        """Detail response includes featured_image (same shape as list)."""
        slug = db_hotel_and_location["location"].slug
        response = client.get(f"/locations/{slug}")
        assert response.status_code == 200
        assert "featured_image" in response.json()
