"""Tests for health and root endpoints."""

from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_root_returns_welcome_message(self, client: TestClient):
        """Should return welcome message."""
        response = client.get("/")

        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to NestStay API"}


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_check_success(self, client: TestClient):
        """Should return healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
