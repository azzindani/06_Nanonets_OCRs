# Test Fixtures

Place your test documents here for OCR testing.

## Supported Formats

- **PDF**: `.pdf` (multi-page supported)
- **Images**: `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`, `.webp`

## Running Tests

```bash
# Run asset-based tests
python -m tests.test_with_assets
```

## What the Tests Do

1. **Multi-page Support**: Extracts all pages from PDFs
2. **Image Processing**: Validates preprocessing and resizing
3. **Bounding Box Visualization**: Creates annotated output images
4. **Field Extraction**: Extracts 50+ document fields
5. **Format Conversion**: Generates JSON, XML, HTML, CSV outputs

## Outputs

Test outputs are saved to `tests/fixtures/outputs/`:
- `bbox_visualization.png` - Bounding box visualization
- `output.json` - JSON format
- `output.xml` - XML format
- `output.html` - HTML preview
- `output.csv` - CSV format

## Notes

- If no assets are found, synthetic test documents are generated
- Place your actual documents here for real-world testing
- All documents in this folder are gitignored by default
