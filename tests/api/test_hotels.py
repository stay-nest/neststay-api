"""Tests for hotel API endpoints."""

from fastapi.testclient import TestClient


class TestListHotels:
    """Tests for GET /hotels/ endpoint."""

    def test_list_hotels_empty(self, client: TestClient):
        """Should return empty list when no hotels exist."""
        response = client.get("/hotels/")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    def test_list_hotels_with_data(self, client: TestClient, sample_hotel_data: dict):
        """Should return list of hotels."""
        # Create a hotel first
        client.post("/hotels/", json=sample_hotel_data)

        response = client.get("/hotels/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["name"] == sample_hotel_data["name"]

    def test_list_hotels_pagination(self, client: TestClient):
        """Should paginate results correctly."""
        # Create 3 hotels
        for i in range(3):
            client.post(
                "/hotels/",
                json={
                    "name": f"Hotel {i}",
                    "description": f"Description {i}",
                    "contact_phone": f"+123456789{i}",
                    "contact_email": f"hotel{i}@test.com",
                },
            )

        # Get first page with page_size=2
        response = client.get("/hotels/?page=1&page_size=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["page_size"] == 2

        # Get second page
        response = client.get("/hotels/?page=2&page_size=2")
        data = response.json()
        assert len(data["items"]) == 1
        assert data["page"] == 2


class TestCreateHotel:
    """Tests for POST /hotels/ endpoint."""

    def test_create_hotel_success(self, client: TestClient, sample_hotel_data: dict):
        """Should create a hotel successfully."""
        response = client.post("/hotels/", json=sample_hotel_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_hotel_data["name"]
        assert data["description"] == sample_hotel_data["description"]
        assert "slug" in data
        assert data["is_active"] is True

    def test_create_hotel_generates_slug(
        self, client: TestClient, sample_hotel_data: dict
    ):
        """Should generate a unique slug for the hotel."""
        response = client.post("/hotels/", json=sample_hotel_data)

        assert response.status_code == 201
        data = response.json()
        assert data["slug"].startswith("test-hotel-")

    def test_create_hotel_missing_required_field(self, client: TestClient):
        """Should return 422 when required field is missing."""
        incomplete_data = {
            "name": "Test Hotel",
            # missing contact_phone
        }

        response = client.post("/hotels/", json=incomplete_data)

        assert response.status_code == 422

    def test_create_hotel_with_all_required_fields(self, client: TestClient):
        """Should create hotel with all required fields."""
        data = {
            "name": "Minimal Hotel",
            "description": "A minimal hotel",
            "contact_phone": "+1234567890",
            "contact_email": "minimal@hotel.com",
        }

        response = client.post("/hotels/", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "Minimal Hotel"


class TestGetHotel:
    """Tests for GET /hotels/{slug} endpoint."""

    def test_get_hotel_success(self, client: TestClient, created_hotel: dict):
        """Should return hotel by slug."""
        slug = created_hotel["slug"]

        response = client.get(f"/hotels/{slug}")

        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == slug
        assert data["name"] == created_hotel["name"]

    def test_get_hotel_not_found(self, client: TestClient):
        """Should return 404 for non-existent hotel."""
        response = client.get("/hotels/non-existent-slug")

        assert response.status_code == 404


class TestUpdateHotel:
    """Tests for PUT /hotels/{slug} endpoint."""

    def test_update_hotel_success(self, client: TestClient, created_hotel: dict):
        """Should update hotel successfully."""
        slug = created_hotel["slug"]
        update_data = {"name": "Updated Hotel Name"}

        response = client.put(f"/hotels/{slug}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Hotel Name"
        # Slug should remain the same
        assert data["slug"] == slug

    def test_update_hotel_partial(self, client: TestClient, created_hotel: dict):
        """Should allow partial updates."""
        slug = created_hotel["slug"]
        update_data = {"description": "New description"}

        response = client.put(f"/hotels/{slug}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New description"
        assert data["name"] == created_hotel["name"]

    def test_update_hotel_not_found(self, client: TestClient):
        """Should return 404 for non-existent hotel."""
        response = client.put(
            "/hotels/non-existent-slug", json={"name": "Updated Name"}
        )

        assert response.status_code == 404


class TestDeleteHotel:
    """Tests for DELETE /hotels/{slug} endpoint."""

    def test_delete_hotel_success(self, client: TestClient, created_hotel: dict):
        """Should soft delete hotel successfully."""
        slug = created_hotel["slug"]

        response = client.delete(f"/hotels/{slug}")

        assert response.status_code == 204

        # Verify hotel is no longer accessible
        get_response = client.get(f"/hotels/{slug}")
        assert get_response.status_code == 404

    def test_delete_hotel_not_found(self, client: TestClient):
        """Should return 404 for non-existent hotel."""
        response = client.delete("/hotels/non-existent-slug")

        assert response.status_code == 404

    def test_deleted_hotel_not_in_list(
        self, client: TestClient, sample_hotel_data: dict
    ):
        """Deleted hotel should not appear in list."""
        # Create and delete a hotel
        create_response = client.post("/hotels/", json=sample_hotel_data)
        slug = create_response.json()["slug"]
        client.delete(f"/hotels/{slug}")

        # List should be empty
        response = client.get("/hotels/")
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
