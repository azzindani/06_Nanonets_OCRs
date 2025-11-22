"""Tests for document classifier."""
import pytest
from core.document_classifier import (
    DocumentClassifier,
    DocumentType,
    ClassificationResult,
    get_document_classifier
)


class TestDocumentClassifier:
    """Test document classification functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = DocumentClassifier()

    def test_classify_invoice(self):
        """Test classification of invoice text."""
        text = """
        INVOICE
        Invoice Number: INV-2024-001
        Invoice Date: January 15, 2024
        Due Date: February 15, 2024

        Bill To:
        John Smith
        123 Main Street

        Item        Qty    Unit Price    Amount
        Widget A    10     $50.00        $500.00
        Widget B    5      $75.00        $375.00

        Subtotal: $875.00
        Tax (8%): $70.00
        Total Due: $945.00

        Payment Terms: Net 30
        """
        result = self.classifier.classify(text)

        assert isinstance(result, ClassificationResult)
        assert result.document_type == DocumentType.INVOICE
        assert result.confidence > 0.5
        assert "invoice" in result.keywords_found

    def test_classify_receipt(self):
        """Test classification of receipt text."""
        text = """
        STORE RECEIPT
        Transaction ID: 12345
        Date: 2024-01-15 14:30

        Items:
        Coffee          $4.50
        Sandwich        $8.99

        Subtotal: $13.49
        Tax: $1.08
        Total: $14.57

        Paid by Credit Card
        Change: $0.00

        Thank you for shopping!
        Cashier: Jane
        """
        result = self.classifier.classify(text)

        assert result.document_type == DocumentType.RECEIPT
        assert result.confidence > 0.3

    def test_classify_contract(self):
        """Test classification of contract text."""
        text = """
        SERVICE AGREEMENT

        This Agreement is entered into as of January 1, 2024.

        WHEREAS the parties wish to establish terms and conditions,

        The parties hereby agree to the following binding terms:

        1. Term and Termination
        The effective date of this contract shall be...

        2. Covenant
        Both parties covenant to fulfill their obligations...

        IN WITNESS WHEREOF, the parties have executed this Agreement.

        Signature: _______________
        """
        result = self.classifier.classify(text)

        assert result.document_type == DocumentType.CONTRACT
        assert "agreement" in result.keywords_found or "contract" in result.keywords_found

    def test_classify_medical(self):
        """Test classification of medical document."""
        text = """
        PATIENT INFORMATION
        Patient Name: Jane Doe
        Patient ID: P-12345
        Date of Service: 2024-01-15

        Diagnosis: Acute bronchitis

        Prescription:
        Medication: Amoxicillin
        Dosage: 500mg twice daily

        Treatment Plan:
        Rest and increased fluids

        Dr. Smith, MD
        City Hospital Clinic
        """
        result = self.classifier.classify(text)

        assert result.document_type == DocumentType.MEDICAL
        assert result.confidence > 0.3

    def test_classify_bank_statement(self):
        """Test classification of bank statement."""
        text = """
        BANK STATEMENT
        Account Number: 1234567890
        Statement Period: January 1-31, 2024

        Opening Balance: $5,000.00

        Transactions:
        01/05 Deposit    +$2,000.00
        01/10 Withdrawal -$500.00
        01/15 Interest   +$5.25

        Closing Balance: $6,505.25
        """
        result = self.classifier.classify(text)

        assert result.document_type == DocumentType.BANK_STATEMENT

    def test_classify_unknown(self):
        """Test classification of unrecognizable text."""
        text = "xyz abc 123 random text without patterns"
        result = self.classifier.classify(text)

        assert result.document_type == DocumentType.UNKNOWN
        assert result.confidence == 0.0

    def test_classify_empty_text(self):
        """Test classification of empty text."""
        result = self.classifier.classify("")

        assert result.document_type == DocumentType.UNKNOWN
        assert result.confidence == 0.0

    def test_classify_with_routing(self):
        """Test classification with schema routing."""
        text = "Invoice Number: 123, Total Due: $500"
        result, schema = self.classifier.classify_with_routing(text)

        assert isinstance(result, ClassificationResult)
        assert isinstance(schema, str)

    def test_get_supported_types(self):
        """Test getting supported document types."""
        types = self.classifier.get_supported_types()

        assert isinstance(types, list)
        assert len(types) > 0
        assert "invoice" in types
        assert "receipt" in types
        assert "unknown" not in types

    def test_all_scores_populated(self):
        """Test that all document type scores are populated."""
        text = "Invoice Number: 123"
        result = self.classifier.classify(text)

        assert len(result.all_scores) > 0
        for score in result.all_scores.values():
            assert 0 <= score <= 1

    def test_singleton_instance(self):
        """Test singleton pattern."""
        classifier1 = get_document_classifier()
        classifier2 = get_document_classifier()

        assert classifier1 is classifier2


class TestDocumentType:
    """Test DocumentType enum."""

    def test_all_document_types(self):
        """Test all document types are defined."""
        assert DocumentType.INVOICE.value == "invoice"
        assert DocumentType.RECEIPT.value == "receipt"
        assert DocumentType.CONTRACT.value == "contract"
        assert DocumentType.FORM.value == "form"
        assert DocumentType.LETTER.value == "letter"
        assert DocumentType.REPORT.value == "report"
        assert DocumentType.ID_DOCUMENT.value == "id_document"
        assert DocumentType.BANK_STATEMENT.value == "bank_statement"
        assert DocumentType.TAX_DOCUMENT.value == "tax_document"
        assert DocumentType.MEDICAL.value == "medical"
        assert DocumentType.UNKNOWN.value == "unknown"
