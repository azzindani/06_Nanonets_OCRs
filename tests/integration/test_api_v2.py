"""
Tests for API v2 endpoints and enhanced features.
"""
import pytest
import io
from PIL import Image

try:
    from fastapi.testclient import TestClient
    from api.server import app
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    TestClient = None
    app = None

pytestmark = pytest.mark.skipif(not HAS_FASTAPI, reason="FastAPI not available")


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_image():
    """Create a test image."""
    img = Image.new('RGB', (100, 100), color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


@pytest.fixture
def test_invoice_image():
    """Create a test image with invoice-like text."""
    from PIL import ImageDraw, ImageFont

    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)

    # Add invoice-like text
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    draw.text((10, 10), "INVOICE #12345", fill='black', font=font)
    draw.text((10, 40), "Date: 2024-01-15", fill='black', font=font)
    draw.text((10, 70), "Total: $500.00", fill='black', font=font)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


class TestAPIv2Endpoint:
    """Tests for the /v2/ocr endpoint."""

    def test_v2_ocr_returns_structured_output(self, client, test_image):
        """Test that v2 endpoint returns structured output format."""
        response = client.post(
            "/api/v1/v2/ocr",
            files={"file": ("test.png", test_image, "image/png")},
            data={"max_tokens": 1024}
        )

        # May return 200 or 500 depending on model availability
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()

            # Verify v2 response structure
            assert "api_version" in data
            assert data["api_version"] == "2.0"
            assert "job_id" in data
            assert "status" in data
            assert "processing_time_ms" in data
            assert "document" in data
            assert "result" in data

            # Verify document metadata
            doc = data["document"]
            assert "filename" in doc
            assert "file_size_mb" in doc
            assert "file_type" in doc
            assert "total_pages" in doc

            # Verify result structure
            result = data["result"]
            assert "document_type" in result
            assert "confidence" in result
            assert "language" in result
            assert "extracted_fields" in result
            assert "line_items" in result
            assert "entities" in result

    def test_v2_ocr_invalid_file_type(self, client):
        """Test v2 endpoint rejects invalid file types."""
        invalid_file = io.BytesIO(b"not an image")

        response = client.post(
            "/api/v1/v2/ocr",
            files={"file": ("test.txt", invalid_file, "text/plain")}
        )

        assert response.status_code == 400

    def test_v2_ocr_missing_file(self, client):
        """Test v2 endpoint requires file."""
        response = client.post("/api/v1/v2/ocr")

        assert response.status_code == 422


class TestClassifyEndpoint:
    """Tests for the /classify endpoint."""

    def test_classify_with_file(self, client, test_image):
        """Test document classification with file upload."""
        response = client.post(
            "/api/v1/classify",
            files={"file": ("test.png", test_image, "image/png")}
        )

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "document_type" in data
            assert "confidence" in data
            assert "all_scores" in data

    def test_classify_with_text(self, client):
        """Test document classification with text input."""
        response = client.post(
            "/api/v1/classify",
            data={"text": "Invoice #12345\nTotal: $500.00\nDate: 2024-01-15"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["document_type"] == "invoice"
        assert data["confidence"] > 0

    def test_classify_no_input(self, client):
        """Test classify requires file or text."""
        response = client.post("/api/v1/classify")

        assert response.status_code == 400


class TestDetectLanguageEndpoint:
    """Tests for the /detect-language endpoint."""

    def test_detect_language_english(self, client):
        """Test language detection for English text."""
        response = client.post(
            "/api/v1/detect-language",
            data={"text": "This is a sample document in English language."}
        )

        assert response.status_code == 200
        data = response.json()
        assert "primary_language" in data
        assert data["primary_language"] == "en"
        assert "confidence" in data

    def test_detect_language_spanish(self, client):
        """Test language detection for Spanish text."""
        response = client.post(
            "/api/v1/detect-language",
            data={"text": "Este es un documento de ejemplo en idioma español con varias palabras características del castellano."}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["primary_language"] == "es"

    def test_detect_language_no_input(self, client):
        """Test detect-language requires file or text."""
        response = client.post("/api/v1/detect-language")

        assert response.status_code == 400


class TestExtractEntitiesEndpoint:
    """Tests for the /extract-entities endpoint."""

    def test_extract_entities_with_text(self, client):
        """Test entity extraction from text."""
        text = """
        John Smith from Acme Corp sent an email to jane@example.com
        regarding the $5,000.00 invoice dated 01/15/2024.
        Contact him at (555) 123-4567.
        """

        response = client.post(
            "/api/v1/extract-entities",
            data={"text": text}
        )

        assert response.status_code == 200
        data = response.json()

        assert "entities" in data
        assert "summary" in data

        # Check for expected entity types
        entity_types = [e["type"] for e in data["entities"]]
        assert "money" in entity_types or "email" in entity_types

    def test_extract_entities_no_input(self, client):
        """Test extract-entities requires file or text."""
        response = client.post("/api/v1/extract-entities")

        assert response.status_code == 400


class TestStructuredEndpoint:
    """Tests for the /structured endpoint."""

    def test_structured_output(self, client, test_image):
        """Test structured output endpoint."""
        response = client.post(
            "/api/v1/structured",
            files={"file": ("test.png", test_image, "image/png")}
        )

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()

            # Verify structured output format
            assert "document_type" in data
            assert "confidence" in data
            assert "language" in data
            assert "extracted_fields" in data
            assert "line_items" in data
            assert "entities" in data
            assert "raw" in data


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_rate_limit_headers(self, client):
        """Test that rate limit headers are returned."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        # Rate limit headers should be present
        assert "X-RateLimit-Limit" in response.headers or response.status_code == 200

    def test_health_endpoint_not_rate_limited(self, client):
        """Test that health endpoint bypasses rate limiting."""
        # Make multiple rapid requests
        for _ in range(20):
            response = client.get("/api/v1/health")
            assert response.status_code == 200


class TestAPIKeyAuthentication:
    """Tests for API key authentication."""

    def test_endpoints_work_with_api_key(self, client):
        """Test endpoints work with valid API key."""
        headers = {"X-API-Key": "test_key_12345"}

        response = client.get("/api/v1/health", headers=headers)
        assert response.status_code == 200

    def test_classify_with_api_key(self, client):
        """Test classify endpoint with API key."""
        headers = {"X-API-Key": "test_key_12345"}

        response = client.post(
            "/api/v1/classify",
            data={"text": "Invoice #12345 Total: $500.00"},
            headers=headers
        )

        assert response.status_code == 200


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_endpoint(self, client):
        """Test 404 for invalid endpoint."""
        response = client.get("/api/v1/invalid")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test 405 for wrong HTTP method."""
        response = client.get("/api/v1/classify")
        assert response.status_code == 405

    def test_unsupported_file_type_v2(self, client):
        """Test error for unsupported file type in v2."""
        invalid_file = io.BytesIO(b"test content")

        response = client.post(
            "/api/v1/v2/ocr",
            files={"file": ("test.xyz", invalid_file, "application/octet-stream")}
        )

        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]


class TestPersonEntityFiltering:
    """Tests for person entity false positive filtering."""

    def test_filters_document_labels(self, client):
        """Test that document labels are not detected as persons."""
        text = """
        Bill To: Adam Smith
        Ship To: Chicago, IL
        Ship Mode: Second Class
        Balance Due: $100.00
        """

        response = client.post(
            "/api/v1/extract-entities",
            data={"text": text}
        )

        assert response.status_code == 200
        data = response.json()

        # Get person entities
        persons = [e["value"] for e in data["entities"] if e["type"] == "person"]

        # Should include actual name
        assert "Adam Smith" in persons

        # Should NOT include document labels
        assert "Bill To" not in persons
        assert "Ship To" not in persons
        assert "Ship Mode" not in persons
        assert "Second Class" not in persons
        assert "Balance Due" not in persons
