"""
Comprehensive test for core OCR components.

Run with: python -m core.test_complete_ocr
"""
import sys
import time
from datetime import datetime


def test_config():
    """Test configuration loading."""
    print("\n[1/7] Testing Configuration...")
    try:
        from config import settings, PREDEFINED_FIELDS, DEFAULT_OCR_PROMPT

        assert settings.model.name, "Model name not set"
        assert settings.processing.max_tokens > 0, "Invalid max tokens"
        assert len(PREDEFINED_FIELDS) > 0, "No predefined fields"
        assert DEFAULT_OCR_PROMPT, "No default prompt"

        print(f"  ✓ Model: {settings.model.name}")
        print(f"  ✓ Max tokens: {settings.processing.max_tokens}")
        print(f"  ✓ Predefined fields: {len(PREDEFINED_FIELDS)}")
        return True
    except Exception as e:
        print(f"  ✗ Config test failed: {e}")
        return False


def test_output_parser():
    """Test output parser."""
    print("\n[2/7] Testing Output Parser...")
    try:
        from core.output_parser import OutputParser

        parser = OutputParser()

        sample = """
        --- Page 1 ---
        Invoice Number: INV-001

        <table><tr><td>Item</td><td>Price</td></tr></table>

        $E = mc^2$

        <img>Company logo</img>
        <watermark>DRAFT</watermark>
        <page_number>1/5</page_number>

        ☑ Approved
        ☐ Pending
        """

        result = parser.parse(sample)

        assert len(result.pages) == 1, "Expected 1 page"
        page = result.pages[0]

        assert len(page.tables_html) == 1, "Expected 1 table"
        assert len(page.latex_equations) >= 1, "Expected equations"
        assert len(page.image_descriptions) == 1, "Expected 1 image"
        assert len(page.watermarks) == 1, "Expected 1 watermark"
        assert len(page.checkboxes) == 2, "Expected 2 checkboxes"

        print(f"  ✓ Tables: {len(page.tables_html)}")
        print(f"  ✓ Equations: {len(page.latex_equations)}")
        print(f"  ✓ Images: {len(page.image_descriptions)}")
        print(f"  ✓ Watermarks: {len(page.watermarks)}")
        print(f"  ✓ Checkboxes: {len(page.checkboxes)}")
        return True
    except Exception as e:
        print(f"  ✗ Output parser test failed: {e}")
        return False


def test_field_extractor():
    """Test field extractor."""
    print("\n[3/7] Testing Field Extractor...")
    try:
        from core.field_extractor import FieldExtractor

        extractor = FieldExtractor()

        text = """
        Company Name: Acme Corporation
        Invoice Number: INV-2024-001
        Invoice Date: 2024-01-15
        Total Amount: $1,234.56
        Due Date: 2024-02-15
        """

        fields = ["Company Name", "Invoice Number", "Invoice Date",
                  "Total Amount", "Due Date", "PO Number"]

        results = extractor.extract(text, enabled_fields=fields)

        found = sum(1 for r in results.values() if r.found)

        assert results["Company Name"].found, "Company Name not found"
        assert results["Invoice Number"].found, "Invoice Number not found"
        assert "Acme" in results["Company Name"].value, "Wrong company name"

        stats = extractor.get_statistics(results)

        print(f"  ✓ Fields found: {found}/{len(fields)}")
        print(f"  ✓ Success rate: {stats['success_rate']}%")
        print(f"  ✓ Company: {results['Company Name'].value}")
        print(f"  ✓ Invoice: {results['Invoice Number'].value}")
        return True
    except Exception as e:
        print(f"  ✗ Field extractor test failed: {e}")
        return False


def test_format_converter():
    """Test format converter."""
    print("\n[4/7] Testing Format Converter...")
    try:
        from core.output_parser import OutputParser
        from core.format_converter import FormatConverter

        parser = OutputParser()
        converter = FormatConverter()

        sample = """
        --- Page 1 ---
        Test content with table:
        <table><tr><td>Data</td></tr></table>
        """

        parsed = parser.parse(sample)

        # Test JSON
        json_out = converter.to_json(parsed)
        assert "pages" in json_out, "JSON missing pages"
        assert "Test content" in json_out, "JSON missing content"

        # Test XML
        xml_out = converter.to_xml(parsed)
        assert "<DocumentOCR>" in xml_out, "XML missing root"
        assert "<Page" in xml_out, "XML missing page"

        # Test HTML
        html_out = converter.to_html(parsed)
        assert "Document Preview" in html_out, "HTML missing preview"

        print(f"  ✓ JSON output: {len(json_out)} chars")
        print(f"  ✓ XML output: {len(xml_out)} chars")
        print(f"  ✓ HTML output: {len(html_out)} chars")
        return True
    except Exception as e:
        print(f"  ✗ Format converter test failed: {e}")
        return False


def test_document_processor():
    """Test document processor."""
    print("\n[5/7] Testing Document Processor...")
    try:
        from core.document_processor import DocumentProcessor
        from PIL import Image
        import tempfile
        import os

        processor = DocumentProcessor()

        # Test validation with actual temp files
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_pdf = f.name
            f.write(b'%PDF-1.4 test')

        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            temp_xyz = f.name
            f.write(b'test')

        try:
            result = processor.validate_file(temp_pdf)
            assert result.is_valid, "PDF should be valid"

            result = processor.validate_file(temp_xyz)
            assert not result.is_valid, "XYZ should be invalid"
        finally:
            os.unlink(temp_pdf)
            os.unlink(temp_xyz)

        # Test image resize
        large_img = Image.new('RGB', (3000, 2000), 'white')
        resized = processor.preprocess_image(large_img, 1536)

        assert resized.size[0] == 1536, "Width should be 1536"
        assert resized.size[1] == 1024, "Height should maintain ratio"

        print(f"  ✓ PDF validation: valid")
        print(f"  ✓ XYZ validation: invalid (correct)")
        print(f"  ✓ Image resize: {large_img.size} -> {resized.size}")
        return True
    except Exception as e:
        print(f"  ✗ Document processor test failed: {e}")
        return False


def test_services():
    """Test services (cache, queue, storage)."""
    print("\n[6/7] Testing Services...")
    try:
        # Cache
        from services.cache import CacheService
        cache = CacheService()
        cache.set("test_key", {"data": "value"})
        result = cache.get("test_key")
        assert result["data"] == "value", "Cache get failed"
        cache.delete("test_key")
        print("  ✓ Cache service: OK")

        # Queue
        from services.queue import JobQueue
        queue = JobQueue()
        job_id = queue.enqueue("test", {"file": "test.pdf"})
        status = queue.get_job_status(job_id)
        assert status["status"] == "pending", "Job should be pending"
        print("  ✓ Job queue: OK")

        # Storage
        import tempfile
        from services.storage import StorageService
        with tempfile.TemporaryDirectory() as tmp:
            storage = StorageService(tmp)
            stored = storage.save_upload("test.txt", b"content")
            retrieved = storage.get_upload(stored.file_id)
            assert retrieved == b"content", "Storage get failed"
            storage.delete_upload(stored.file_id)
        print("  ✓ Storage service: OK")

        return True
    except Exception as e:
        print(f"  ✗ Services test failed: {e}")
        return False


def test_validators():
    """Test validators."""
    print("\n[7/7] Testing Validators...")
    try:
        from utils.validators import (
            validate_api_key, validate_url,
            validate_max_tokens, sanitize_filename
        )

        # API key
        valid, _ = validate_api_key("valid-api-key-12345")
        assert valid, "Valid key should pass"

        valid, _ = validate_api_key("short")
        assert not valid, "Short key should fail"

        # URL
        valid, _ = validate_url("https://example.com/api")
        assert valid, "Valid URL should pass"

        # Max tokens
        valid, _ = validate_max_tokens(2048)
        assert valid, "2048 tokens should be valid"

        # Sanitize
        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result, "Path traversal should be removed"

        print("  ✓ API key validation: OK")
        print("  ✓ URL validation: OK")
        print("  ✓ Token validation: OK")
        print("  ✓ Filename sanitization: OK")
        return True
    except Exception as e:
        print(f"  ✗ Validators test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("NANONETS VL - COMPLETE SYSTEM TEST")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    start_time = time.time()

    tests = [
        test_config,
        test_output_parser,
        test_field_extractor,
        test_format_converter,
        test_document_processor,
        test_services,
        test_validators,
    ]

    results = []
    for test in tests:
        results.append(test())

    elapsed = time.time() - start_time
    passed = sum(results)
    total = len(results)

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"  Passed: {passed}/{total}")
    print(f"  Failed: {total - passed}/{total}")
    print(f"  Time: {elapsed:.2f}s")
    print("=" * 60)

    if passed == total:
        print("✓ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
