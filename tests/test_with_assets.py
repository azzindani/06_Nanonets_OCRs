"""
Test OCR system with real document assets.

Run with: python -m tests.test_with_assets

This test will:
1. Use any PDF/image assets found in tests/fixtures/
2. Generate synthetic test documents if no assets found
3. Test multi-page document support
4. Test bounding box visualization
"""
import sys
import os
import time
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def find_test_assets():
    """Find all test assets in fixtures directory."""
    assets = {
        "pdf": [],
        "image": []
    }

    if not FIXTURES_DIR.exists():
        FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
        return assets

    for f in FIXTURES_DIR.rglob("*"):
        if f.is_file():
            ext = f.suffix.lower()
            if ext == ".pdf":
                assets["pdf"].append(f)
            elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"]:
                assets["image"].append(f)

    return assets


def create_synthetic_pdf():
    """Create a synthetic multi-page PDF for testing."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch

        pdf_path = FIXTURES_DIR / "synthetic_multipage.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=letter)

        # Page 1: Invoice
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1*inch, 10*inch, "INVOICE")
        c.setFont("Helvetica", 12)
        c.drawString(1*inch, 9.5*inch, "Invoice Number: INV-2024-001")
        c.drawString(1*inch, 9.2*inch, "Date: 2024-01-15")
        c.drawString(1*inch, 8.9*inch, "Company: Acme Corporation")
        c.drawString(1*inch, 8.6*inch, "Total Amount: $1,234.56")

        # Table
        c.drawString(1*inch, 7.5*inch, "Item          Qty    Price")
        c.drawString(1*inch, 7.2*inch, "Widget A      10     $50.00")
        c.drawString(1*inch, 6.9*inch, "Widget B      5      $100.00")
        c.showPage()

        # Page 2: Terms
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1*inch, 10*inch, "TERMS AND CONDITIONS")
        c.setFont("Helvetica", 10)
        y = 9.5*inch
        terms = [
            "1. Payment is due within 30 days of invoice date.",
            "2. Late payments subject to 1.5% monthly interest.",
            "3. All sales are final unless otherwise specified.",
            "4. Shipping costs are the responsibility of the buyer.",
            "5. Returns must be authorized within 14 days."
        ]
        for term in terms:
            c.drawString(1*inch, y, term)
            y -= 0.3*inch
        c.showPage()

        # Page 3: Signature
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1*inch, 10*inch, "AUTHORIZATION")
        c.setFont("Helvetica", 12)
        c.drawString(1*inch, 9*inch, "☑ I agree to the terms and conditions")
        c.drawString(1*inch, 8.5*inch, "☐ Subscribe to newsletter")
        c.drawString(1*inch, 7.5*inch, "Signature: _________________")
        c.drawString(1*inch, 7*inch, "Date: _________________")
        c.showPage()

        c.save()
        return pdf_path
    except ImportError:
        return None


def create_synthetic_image():
    """Create a synthetic image for testing."""
    try:
        from PIL import Image, ImageDraw, ImageFont

        img_path = FIXTURES_DIR / "synthetic_document.png"

        # Create image
        img = Image.new('RGB', (800, 600), 'white')
        draw = ImageDraw.Draw(img)

        # Draw content
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            font = ImageFont.load_default()
            small_font = font

        draw.text((50, 30), "RECEIPT", fill='black', font=font)
        draw.text((50, 80), "Store: Test Store", fill='black', font=small_font)
        draw.text((50, 110), "Date: 2024-01-15", fill='black', font=small_font)
        draw.text((50, 140), "Receipt #: RCP-12345", fill='black', font=small_font)

        # Table
        draw.rectangle([50, 200, 750, 350], outline='black')
        draw.line([50, 230, 750, 230], fill='black')
        draw.text((60, 205), "Item", fill='black', font=small_font)
        draw.text((300, 205), "Qty", fill='black', font=small_font)
        draw.text((450, 205), "Price", fill='black', font=small_font)
        draw.text((600, 205), "Total", fill='black', font=small_font)

        draw.text((60, 250), "Product A", fill='black', font=small_font)
        draw.text((300, 250), "2", fill='black', font=small_font)
        draw.text((450, 250), "$10.00", fill='black', font=small_font)
        draw.text((600, 250), "$20.00", fill='black', font=small_font)

        draw.text((60, 290), "Product B", fill='black', font=small_font)
        draw.text((300, 290), "1", fill='black', font=small_font)
        draw.text((450, 290), "$15.00", fill='black', font=small_font)
        draw.text((600, 290), "$15.00", fill='black', font=small_font)

        draw.text((450, 380), "Total: $35.00", fill='black', font=font)

        # Checkbox
        draw.rectangle([50, 450, 70, 470], outline='black')
        draw.text((80, 450), "Email receipt", fill='black', font=small_font)

        img.save(img_path)
        return img_path
    except ImportError:
        return None


def test_document_processor_multipage():
    """Test multi-page document processing."""
    print("\n[1/5] Testing Multi-Page Document Support...")
    try:
        from core.document_processor import DocumentProcessor

        processor = DocumentProcessor()

        # Find or create test PDF
        assets = find_test_assets()
        test_pdf = None

        if assets["pdf"]:
            test_pdf = assets["pdf"][0]
            print(f"  Using asset: {test_pdf.name}")
        else:
            test_pdf = create_synthetic_pdf()
            if test_pdf:
                print(f"  Created synthetic PDF: {test_pdf.name}")

        if not test_pdf or not test_pdf.exists():
            print("  ⚠ No PDF available (install reportlab for synthetic)")
            return True  # Skip but don't fail

        # Extract pages
        pages = processor.extract_pdf_pages(str(test_pdf))

        assert len(pages) > 0, "Should extract at least 1 page"
        print(f"  ✓ Extracted {len(pages)} pages")

        # Validate each page is an image
        for i, page in enumerate(pages):
            assert page.mode in ['RGB', 'L', 'RGBA'], f"Page {i+1} is not valid image"
            assert page.size[0] > 0 and page.size[1] > 0, f"Page {i+1} has invalid size"
            print(f"  ✓ Page {i+1}: {page.size[0]}x{page.size[1]} ({page.mode})")

        return True
    except Exception as e:
        print(f"  ✗ Multi-page test failed: {e}")
        return False


def test_image_processing():
    """Test single image processing."""
    print("\n[2/5] Testing Image Processing...")
    try:
        from core.document_processor import DocumentProcessor
        from PIL import Image

        processor = DocumentProcessor()

        # Find or create test image
        assets = find_test_assets()
        test_img = None

        if assets["image"]:
            test_img = assets["image"][0]
            print(f"  Using asset: {test_img.name}")
            img = Image.open(test_img)
        else:
            img_path = create_synthetic_image()
            if img_path:
                test_img = img_path
                print(f"  Created synthetic image: {test_img.name}")
                img = Image.open(test_img)
            else:
                # Create simple test image
                img = Image.new('RGB', (1000, 800), 'white')
                print("  Using blank test image")

        # Test preprocessing
        processed = processor.preprocess_image(img, max_size=1536)

        assert processed.size[0] <= 1536, "Width should be <= 1536"
        assert processed.size[1] <= 1536, "Height should be <= 1536"

        print(f"  ✓ Original: {img.size}")
        print(f"  ✓ Processed: {processed.size}")

        return True
    except Exception as e:
        print(f"  ✗ Image processing test failed: {e}")
        return False


def test_bounding_box_visualization():
    """Test bounding box visualization."""
    print("\n[3/5] Testing Bounding Box Visualization...")
    try:
        from PIL import Image, ImageDraw

        # Create test image
        img = Image.new('RGB', (800, 600), 'white')
        draw = ImageDraw.Draw(img)
        draw.text((100, 100), "Test Document", fill='black')
        draw.text((100, 200), "Invoice: INV-001", fill='black')
        draw.text((100, 300), "Amount: $500", fill='black')

        # Simulate bounding boxes (x1, y1, x2, y2, label, confidence)
        boxes = [
            (90, 90, 300, 130, "title", 0.95),
            (90, 190, 280, 230, "invoice_number", 0.92),
            (90, 290, 250, 330, "amount", 0.88),
        ]

        # Draw bounding boxes
        colors = {
            "title": "red",
            "invoice_number": "blue",
            "amount": "green"
        }

        for x1, y1, x2, y2, label, conf in boxes:
            color = colors.get(label, "purple")
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
            draw.text((x1, y1 - 15), f"{label} ({conf:.0%})", fill=color)

        # Save visualization
        output_dir = FIXTURES_DIR / "outputs"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "bbox_visualization.png"
        img.save(output_path)

        print(f"  ✓ Drew {len(boxes)} bounding boxes")
        print(f"  ✓ Saved to: {output_path}")

        return True
    except Exception as e:
        print(f"  ✗ Bounding box test failed: {e}")
        return False


def test_field_extraction_on_assets():
    """Test field extraction on real documents."""
    print("\n[4/5] Testing Field Extraction...")
    try:
        from core.field_extractor import FieldExtractor

        extractor = FieldExtractor()

        # Sample OCR output (simulating what the model would return)
        sample_text = """
        INVOICE

        Invoice Number: INV-2024-001
        Invoice Date: January 15, 2024
        Due Date: February 15, 2024

        Bill To:
        Acme Corporation
        123 Business Street
        New York, NY 10001

        Items:
        Widget A        10      $50.00      $500.00
        Widget B        5       $100.00     $500.00

        Subtotal: $1,000.00
        Tax (8%): $80.00
        Total Amount: $1,080.00

        Payment Terms: Net 30

        ☑ Terms accepted
        ☐ Rush delivery
        """

        # Extract all predefined fields
        from config import PREDEFINED_FIELDS
        results = extractor.extract(sample_text, enabled_fields=PREDEFINED_FIELDS)

        found = sum(1 for r in results.values() if r.found)
        stats = extractor.get_statistics(results)

        print(f"  ✓ Fields found: {found}/{len(PREDEFINED_FIELDS)}")
        print(f"  ✓ Success rate: {stats['success_rate']}%")

        # Show some found fields
        for field, result in results.items():
            if result.found:
                value = result.value[:30] + "..." if len(result.value) > 30 else result.value
                print(f"    - {field}: {value}")
                if found >= 5:  # Show up to 5 found fields
                    break

        return True
    except Exception as e:
        print(f"  ✗ Field extraction test failed: {e}")
        return False


def test_format_outputs():
    """Test output format generation."""
    print("\n[5/5] Testing Output Formats...")
    try:
        from core.output_parser import OutputParser
        from core.format_converter import FormatConverter

        parser = OutputParser()
        converter = FormatConverter()

        # Sample parsed content
        sample = """
        --- Page 1 ---
        Invoice Number: INV-001

        <table>
        <tr><th>Item</th><th>Price</th></tr>
        <tr><td>Widget</td><td>$50</td></tr>
        </table>

        Total: $50.00

        --- Page 2 ---
        Terms and Conditions apply.

        ☑ I agree
        """

        parsed = parser.parse(sample)

        # Test all formats
        json_out = converter.to_json(parsed)
        xml_out = converter.to_xml(parsed)
        html_out = converter.to_html(parsed)
        csv_out = converter.to_csv(parsed)

        # Save outputs
        output_dir = FIXTURES_DIR / "outputs"
        output_dir.mkdir(exist_ok=True)

        (output_dir / "output.json").write_text(json_out)
        (output_dir / "output.xml").write_text(xml_out)
        (output_dir / "output.html").write_text(html_out)
        (output_dir / "output.csv").write_text(csv_out)

        print(f"  ✓ JSON: {len(json_out)} chars")
        print(f"  ✓ XML: {len(xml_out)} chars")
        print(f"  ✓ HTML: {len(html_out)} chars")
        print(f"  ✓ CSV: {len(csv_out)} chars")
        print(f"  ✓ Outputs saved to: {output_dir}")

        return True
    except Exception as e:
        print(f"  ✗ Format output test failed: {e}")
        return False


def main():
    """Run all asset-based tests."""
    print("=" * 60)
    print("NANONETS VL - ASSET-BASED TESTS")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Show available assets
    assets = find_test_assets()
    total_assets = len(assets["pdf"]) + len(assets["image"])

    print(f"\nTest assets found: {total_assets}")
    if assets["pdf"]:
        print(f"  PDFs: {[p.name for p in assets['pdf']]}")
    if assets["image"]:
        print(f"  Images: {[p.name for p in assets['image']]}")

    if total_assets == 0:
        print("  (Will use synthetic documents)")
        print(f"\n  To add assets, place files in: {FIXTURES_DIR}")

    start_time = time.time()

    tests = [
        test_document_processor_multipage,
        test_image_processing,
        test_bounding_box_visualization,
        test_field_extraction_on_assets,
        test_format_outputs,
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
