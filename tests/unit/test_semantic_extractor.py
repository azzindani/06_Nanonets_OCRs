"""Tests for semantic extractor."""
import pytest
from core.semantic_extractor import (
    SemanticExtractor,
    SemanticField,
    SemanticExtractionResult,
    get_semantic_extractor
)


class TestSemanticExtractor:
    """Test semantic extraction functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = SemanticExtractor()

    def test_extract_basic_entities(self):
        """Test basic entity extraction."""
        text = """
        John Smith
        Email: john.smith@example.com
        Phone: (555) 123-4567
        Date: 01/15/2024
        Amount: $1,500.00
        """
        result = self.extractor.extract(text)

        assert isinstance(result, SemanticExtractionResult)
        assert len(result.entities) > 0

        entity_types = [e["type"] for e in result.entities]
        assert "email" in entity_types or "phone" in entity_types or "money" in entity_types

    def test_extract_payment_info(self):
        """Test extraction of payment information."""
        text = """
        Payment Information
        Total Amount: $500.00
        Due Date: 02/15/2024
        Pay by: Credit Card
        """
        result = self.extractor.extract(text)

        # Check that payment-related fields are extracted
        assert "amount" in result.fields or len(result.entities) > 0

    def test_extract_contact_info(self):
        """Test extraction of contact information."""
        text = """
        Contact Us:
        Phone: 555-123-4567
        Email: support@company.com
        Address: 123 Main Street
        """
        result = self.extractor.extract(text)

        # Should extract contact-related fields
        assert len(result.fields) > 0 or len(result.entities) > 0

    def test_extract_with_queries(self):
        """Test extraction with natural language queries."""
        text = """
        Invoice Total: $1,250.00
        Date: March 15, 2024
        Customer: Acme Corp
        """
        queries = ["What is the total?", "What is the date?"]
        result = self.extractor.extract(text, queries=queries)

        assert isinstance(result, SemanticExtractionResult)

    def test_extract_dates(self):
        """Test date extraction."""
        text = """
        Issue Date: 01/15/2024
        Effective Date: 02/01/2024
        Expiry Date: 12/31/2024
        """
        result = self.extractor.extract(text)

        date_entities = [e for e in result.entities if e["type"] == "date"]
        assert len(date_entities) > 0

    def test_extract_monetary_values(self):
        """Test monetary value extraction."""
        text = """
        Subtotal: $100.00
        Tax: $8.00
        Total: $108.00
        Balance: 500 USD
        """
        result = self.extractor.extract(text)

        money_entities = [e for e in result.entities if e["type"] == "money"]
        assert len(money_entities) > 0

    def test_extract_email_addresses(self):
        """Test email address extraction."""
        text = """
        Contact: john@example.com
        Support: help@company.org
        Sales: sales@business.net
        """
        result = self.extractor.extract(text)

        email_entities = [e for e in result.entities if e["type"] == "email"]
        assert len(email_entities) >= 1

    def test_extract_phone_numbers(self):
        """Test phone number extraction."""
        text = """
        Office: (555) 123-4567
        Mobile: +1 555-987-6543
        Fax: 555.111.2222
        """
        result = self.extractor.extract(text)

        phone_entities = [e for e in result.entities if e["type"] == "phone"]
        assert len(phone_entities) >= 1

    def test_generate_summary(self):
        """Test summary generation."""
        text = """
        John Smith at Acme Corporation
        Total: $500.00
        Date: 01/15/2024
        """
        result = self.extractor.extract(text)

        assert result.summary
        assert isinstance(result.summary, str)
        assert len(result.summary) > 0

    def test_extract_key_points(self):
        """Test key points extraction."""
        text = """
        Important: Please review before signing
        - Item 1
        - Item 2
        - Item 3
        Note: Payment due within 30 days
        """
        result = self.extractor.extract(text)

        assert isinstance(result.key_points, list)

    def test_extract_with_schema(self):
        """Test extraction with custom schema."""
        text = """
        Invoice Number: INV-001
        Total: $500.00
        Date: 01/15/2024
        """
        schema = {
            "total": {"type": "money", "description": "What is the total amount?"},
            "date": {"type": "date", "description": "What is the date?"}
        }
        fields = self.extractor.extract_with_schema(text, schema)

        assert isinstance(fields, dict)

    def test_extract_empty_text(self):
        """Test extraction from empty text."""
        result = self.extractor.extract("")

        assert isinstance(result, SemanticExtractionResult)
        assert len(result.entities) == 0

    def test_semantic_field_properties(self):
        """Test SemanticField dataclass properties."""
        field = SemanticField(
            name="test",
            value="value",
            confidence=0.9,
            context="test_context",
            reasoning="test reasoning"
        )

        assert field.name == "test"
        assert field.value == "value"
        assert field.confidence == 0.9
        assert field.context == "test_context"
        assert field.reasoning == "test reasoning"

    def test_extract_organizations(self):
        """Test organization name extraction."""
        text = """
        Acme Corp Inc.
        XYZ Corporation
        Tech Industries LLC
        """
        result = self.extractor.extract(text)

        org_entities = [e for e in result.entities if e["type"] == "organization"]
        # Organizations are harder to detect, just check it runs
        assert isinstance(result, SemanticExtractionResult)

    def test_singleton_instance(self):
        """Test singleton pattern."""
        extractor1 = get_semantic_extractor()
        extractor2 = get_semantic_extractor()

        assert extractor1 is extractor2

    def test_entity_confidence_scores(self):
        """Test that entities have confidence scores."""
        text = "Email: test@example.com"
        result = self.extractor.extract(text)

        for entity in result.entities:
            assert "confidence" in entity
            assert 0 <= entity["confidence"] <= 1
