"""
Integration tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from api.server import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.integration
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "model_loaded" in data
        assert "gpu_available" in data
        assert "version" in data

    @pytest.mark.integration
    def test_models_endpoint(self, client):
        """Test models info endpoint."""
        response = client.get("/api/v1/models")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "device" in data
        assert "is_loaded" in data


class TestRootEndpoint:
    """Tests for root endpoint."""

    @pytest.mark.integration
    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Nanonets VL OCR API"
        assert "version" in data
        assert "docs" in data


class TestWebhookEndpoints:
    """Tests for webhook endpoints."""

    @pytest.mark.integration
    def test_register_webhook(self, client):
        """Test webhook registration."""
        response = client.post(
            "/api/v1/webhooks/register",
            json={
                "url": "https://example.com/webhook",
                "events": ["document.processed"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "webhook_id" in data
        assert data["url"] == "https://example.com/webhook"

    @pytest.mark.integration
    def test_list_webhooks(self, client):
        """Test listing webhooks."""
        # Register a webhook first
        client.post(
            "/api/v1/webhooks/register",
            json={
                "url": "https://example.com/test",
                "events": ["document.processed"]
            }
        )

        response = client.get("/api/v1/webhooks")

        assert response.status_code == 200
        data = response.json()
        assert "webhooks" in data
        assert isinstance(data["webhooks"], list)

    @pytest.mark.integration
    def test_get_webhook_not_found(self, client):
        """Test getting nonexistent webhook."""
        response = client.get("/api/v1/webhooks/nonexistent-id")

        assert response.status_code == 404

    @pytest.mark.integration
    def test_unregister_webhook(self, client):
        """Test unregistering webhook."""
        # Register first
        reg_response = client.post(
            "/api/v1/webhooks/register",
            json={
                "url": "https://example.com/delete-test",
                "events": ["document.processed"]
            }
        )
        webhook_id = reg_response.json()["webhook_id"]

        # Unregister
        response = client.delete(f"/api/v1/webhooks/{webhook_id}")

        assert response.status_code == 200


class TestRateLimiting:
    """Tests for rate limiting."""

    @pytest.mark.integration
    def test_rate_limit_headers(self, client):
        """Test that rate limit headers are present."""
        response = client.get("/")

        # Check for rate limit headers
        assert "x-ratelimit-limit" in response.headers
        assert "x-ratelimit-remaining" in response.headers


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.integration
    def test_404_not_found(self, client):
        """Test 404 error."""
        response = client.get("/nonexistent-endpoint")

        assert response.status_code == 404

    @pytest.mark.integration
    def test_invalid_webhook_data(self, client):
        """Test invalid webhook registration."""
        response = client.post(
            "/api/v1/webhooks/register",
            json={"invalid": "data"}
        )

        assert response.status_code == 422  # Validation error
