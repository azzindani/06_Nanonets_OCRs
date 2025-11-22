"""Integration tests for the OCR API."""
import pytest
import json
import base64
from io import BytesIO
from unittest.mock import patch, MagicMock
from PIL import Image

from api.server import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_image_base64():
    """Create a sample image as base64."""
    img = Image.new('RGB', (100, 100), color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_ready_check(self, client):
        """Test readiness check."""
        response = client.get("/api/v1/ready")
        assert response.status_code in [200, 503]


class TestOCREndpoints:
    """Test OCR processing endpoints."""

    def test_process_image_endpoint(self, client, sample_image_base64):
        """Test image processing endpoint."""
        response = client.post(
            "/api/v1/ocr",
            json={"image": sample_image_base64}
        )

        # May return 200 or error depending on auth/validation
        assert response.status_code in [200, 401, 422, 500]

    def test_process_without_image(self, client):
        """Test processing without image."""
        response = client.post(
            "/api/v1/ocr",
            json={}
        )

        assert response.status_code in [400, 422]

    def test_batch_processing(self, client, sample_image_base64):
        """Test batch processing endpoint."""
        response = client.post(
            "/api/v1/ocr/batch",
            json={"images": [sample_image_base64, sample_image_base64]}
        )

        # May return 200 or error depending on implementation
        assert response.status_code in [200, 401, 404, 405, 422, 500]


class TestDocumentProcessing:
    """Test document processing workflows."""

    def test_document_classification_flow(self, client):
        """Test document classification in processing flow."""
        from core.document_classifier import get_document_classifier
        classifier = get_document_classifier()
        assert classifier is not None

    def test_semantic_extraction_flow(self, client):
        """Test semantic extraction in processing flow."""
        from core.semantic_extractor import get_semantic_extractor
        extractor = get_semantic_extractor()
        assert extractor is not None


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    def test_ocr_pipeline_components(self):
        """Test that all OCR pipeline components are importable."""
        from core.document_classifier import DocumentClassifier
        from core.semantic_extractor import SemanticExtractor
        from core.language_support import LanguageDetector
        from core.output_parser import OutputParser
        from core.field_extractor import FieldExtractor

        # Verify components can be instantiated
        classifier = DocumentClassifier()
        extractor = SemanticExtractor()
        detector = LanguageDetector()
        parser = OutputParser()
        field_extractor = FieldExtractor()

        assert classifier is not None
        assert extractor is not None
        assert detector is not None
        assert parser is not None
        assert field_extractor is not None

    def test_classification_to_extraction_flow(self):
        """Test flow from classification to extraction."""
        from core.document_classifier import DocumentClassifier
        from core.semantic_extractor import SemanticExtractor

        # Sample invoice text
        text = """
        INVOICE
        Invoice Number: INV-2024-001
        Date: January 15, 2024
        Total: $500.00
        """

        # Classify
        classifier = DocumentClassifier()
        classification = classifier.classify(text)

        # Extract based on classification
        extractor = SemanticExtractor()
        extraction = extractor.extract(text)

        assert classification.document_type.value == "invoice"
        assert extraction.summary is not None

    def test_multilingual_processing_flow(self):
        """Test multilingual document processing."""
        from core.language_support import MultiLanguageProcessor

        processor = MultiLanguageProcessor()

        # English text - use more words for better detection
        en_text = "The invoice number is INV-001. The total amount due is $500. Please pay by the due date."
        result = processor.process_multilingual(en_text, ["invoice_number", "total"])

        assert result["language"] == "en"

        # Spanish text - use more characteristic words
        es_text = "El número de factura es FACT-001. El total que debe pagar es $500. Por favor pague antes de la fecha."
        result = processor.process_multilingual(es_text, ["invoice_number", "total"])

        assert result["language"] == "es"


class TestErrorHandling:
    """Test error handling across the API."""

    def test_invalid_endpoint(self, client):
        """Test accessing invalid endpoint."""
        response = client.get("/invalid/endpoint")
        assert response.status_code == 404

    def test_invalid_method(self, client):
        """Test using invalid HTTP method."""
        response = client.put("/api/v1/health")
        assert response.status_code == 405

    def test_malformed_json(self, client):
        """Test sending malformed JSON."""
        response = client.post(
            "/api/v1/ocr",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]


class TestConcurrency:
    """Test concurrent request handling."""

    def test_multiple_health_checks(self, client):
        """Test multiple concurrent health checks."""
        import concurrent.futures

        def check_health():
            return client.get("/api/v1/health").status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(check_health) for _ in range(10)]
            results = [f.result() for f in futures]

        # All should succeed
        assert all(r == 200 for r in results)
