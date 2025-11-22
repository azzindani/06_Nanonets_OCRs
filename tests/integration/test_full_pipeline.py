"""
Integration tests for full OCR pipeline.
"""
import pytest
import tempfile
from PIL import Image

from core.ocr_engine import OCREngine
from core.output_parser import OutputParser
from core.field_extractor import FieldExtractor
from core.format_converter import FormatConverter
from core.document_processor import DocumentProcessor


class TestFullPipeline:
    """Tests for complete OCR pipeline."""

    @pytest.fixture
    def sample_image_file(self):
        """Create a sample image file."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img = Image.new('RGB', (800, 600), color='white')
            img.save(f.name)
            return f.name

    @pytest.fixture
    def sample_pdf_file(self):
        """Create a sample PDF file."""
        import fitz

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((72, 72), "Invoice Number: INV-001\nTotal: $100")
            doc.save(f.name)
            doc.close()
            return f.name

    @pytest.mark.integration
    def test_document_processor_image(self, sample_image_file):
        """Test processing an image file."""
        processor = DocumentProcessor()

        # Validate
        result = processor.validate_file(sample_image_file)
        assert result.is_valid
        assert result.file_type == "image"

        # Get metadata
        metadata = processor.get_file_metadata(sample_image_file)
        assert metadata.file_type == "PNG"
        assert metadata.total_pages == 1

        # Process
        images, meta = processor.process_file(sample_image_file)
        assert len(images) == 1
        assert isinstance(images[0], Image.Image)

    @pytest.mark.integration
    def test_document_processor_pdf(self, sample_pdf_file):
        """Test processing a PDF file."""
        processor = DocumentProcessor()

        # Validate
        result = processor.validate_file(sample_pdf_file)
        assert result.is_valid
        assert result.file_type == "pdf"

        # Get metadata
        metadata = processor.get_file_metadata(sample_pdf_file)
        assert metadata.file_type == "PDF"
        assert metadata.total_pages == 1

        # Extract pages
        images = processor.extract_pdf_pages(sample_pdf_file)
        assert len(images) == 1

    @pytest.mark.integration
    def test_output_parser_with_sample_text(self):
        """Test parsing sample OCR output."""
        parser = OutputParser()

        sample_text = """
        --- Page 1 ---
        Invoice Number: INV-2024-001
        Date: 2024-01-15

        <table>
            <tr><th>Item</th><th>Price</th></tr>
            <tr><td>Widget</td><td>$50</td></tr>
        </table>

        Total: $50

        $E = mc^2$

        <img>Company logo</img>
        <watermark>DRAFT</watermark>
        """

        result = parser.parse(sample_text)

        assert len(result.pages) == 1
        page = result.pages[0]
        assert len(page.tables_html) == 1
        assert len(page.latex_equations) >= 1
        assert len(page.image_descriptions) == 1
        assert len(page.watermarks) == 1

    @pytest.mark.integration
    def test_field_extractor_with_invoice(self):
        """Test field extraction from invoice text."""
        extractor = FieldExtractor()

        invoice_text = """
        Company Name: Acme Corporation
        Invoice Number: INV-2024-001
        Invoice Date: 2024-01-15
        Due Date: 2024-02-15
        Total Amount: $1,234.56
        """

        results = extractor.extract(
            invoice_text,
            enabled_fields=[
                "Company Name",
                "Invoice Number",
                "Invoice Date",
                "Due Date",
                "Total Amount"
            ]
        )

        assert results["Company Name"].found
        assert results["Invoice Number"].found
        assert results["Total Amount"].found
        assert "1,234.56" in results["Total Amount"].value

    @pytest.mark.integration
    def test_format_converter_outputs(self):
        """Test format conversion of parsed output."""
        parser = OutputParser()
        converter = FormatConverter()

        sample = """
        --- Page 1 ---
        Test content
        <table><tr><td>Data</td></tr></table>
        """

        parsed = parser.parse(sample)

        # Test JSON
        json_output = converter.to_json(parsed)
        assert "pages" in json_output
        assert "Test content" in json_output

        # Test XML
        xml_output = converter.to_xml(parsed)
        assert "<DocumentOCR>" in xml_output
        assert "<Page" in xml_output

        # Test HTML
        html_output = converter.to_html(parsed)
        assert "Document Preview" in html_output

    @pytest.mark.integration
    def test_pipeline_end_to_end(self, sample_pdf_file):
        """Test complete pipeline from file to extracted data."""
        # Step 1: Process document
        processor = DocumentProcessor()
        images, metadata = processor.process_file(sample_pdf_file)

        assert len(images) == 1
        assert metadata.file_type == "PDF"

        # Note: Full OCR requires model loading
        # This test verifies the pipeline structure without model

        # Step 2: Simulate OCR output
        simulated_ocr = """
        --- Page 1 ---
        Invoice Number: INV-001
        Total: $100
        """

        # Step 3: Parse output
        parser = OutputParser()
        parsed = parser.parse(simulated_ocr)
        assert len(parsed.pages) == 1

        # Step 4: Extract fields
        extractor = FieldExtractor()
        fields = extractor.extract(
            simulated_ocr,
            enabled_fields=["Invoice Number", "Total"]
        )

        # Step 5: Convert format
        converter = FormatConverter()
        json_output = converter.to_json(parsed)

        assert fields["Invoice Number"].found
        assert "INV-001" in fields["Invoice Number"].value


class TestCacheIntegration:
    """Tests for cache service integration."""

    @pytest.mark.integration
    def test_cache_ocr_result(self):
        """Test caching OCR results."""
        from services.cache import CacheService

        cache = CacheService()

        # Create test data
        file_content = b"test file content"
        params = {"max_tokens": 2048}
        result = {"text": "extracted text", "pages": 1}

        # Cache result
        key = cache.cache_ocr_result(file_content, params, result)
        assert key.startswith("ocr:")

        # Retrieve result
        cached = cache.get_ocr_result(file_content, params)
        assert cached == result


class TestStorageIntegration:
    """Tests for storage service integration."""

    @pytest.mark.integration
    def test_storage_workflow(self):
        """Test complete storage workflow."""
        import tempfile
        from services.storage import StorageService

        with tempfile.TemporaryDirectory() as tmp:
            storage = StorageService(tmp)

            # Save upload
            content = b"Test document content"
            stored = storage.save_upload("test.pdf", content)

            assert stored.file_id
            assert stored.size_bytes == len(content)

            # Retrieve
            retrieved = storage.get_upload(stored.file_id)
            assert retrieved == content

            # Save result
            job_id = "test-job-123"
            result = {"text": "processed", "pages": 1}
            storage.save_result(job_id, result)

            # Get result
            loaded = storage.get_result(job_id)
            assert loaded == result

            # Cleanup
            storage.delete_upload(stored.file_id)
            storage.delete_result(job_id)
