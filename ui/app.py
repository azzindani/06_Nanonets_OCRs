"""
Gradio web interface for document OCR processing.
"""
import gradio as gr
import json
import uuid
import time
import hashlib
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from config import settings, PREDEFINED_FIELDS
from core.ocr_engine import get_ocr_engine
from core.output_parser import OutputParser
from core.field_extractor import FieldExtractor
from core.format_converter import FormatConverter
from core.structured_output import get_structured_processor
from core.document_classifier import get_document_classifier
from core.language_support import get_language_detector


def create_bounding_box_visualization(image: Image.Image, ocr_text: str) -> Image.Image:
    """Create visualization with bounding boxes for detected elements."""
    img_with_boxes = image.copy()
    draw = ImageDraw.Draw(img_with_boxes)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font = ImageFont.load_default()

    colors = {
        'table': (255, 0, 0),
        'equation': (0, 255, 0),
        'image': (0, 0, 255),
        'watermark': (255, 255, 0),
    }

    width, height = img_with_boxes.size

    # Draw indicators for detected elements
    import re
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(ocr_text, 'html.parser')

    if soup.find_all('table'):
        draw.rectangle([(10, 10), (width - 10, height // 3)],
                       outline=colors['table'], width=3)
        draw.text((15, 15), "Table Detected", fill=colors['table'], font=font)

    if re.search(r'\$\$[^$]+\$\$|\$[^$]+\$', ocr_text):
        draw.rectangle([(10, height // 3), (width - 10, 2 * height // 3)],
                       outline=colors['equation'], width=3)
        draw.text((15, height // 3 + 5), "Equation Detected",
                  fill=colors['equation'], font=font)

    if re.search(r'<img>.*?</img>', ocr_text):
        draw.rectangle([(10, 2 * height // 3), (width - 10, height - 10)],
                       outline=colors['image'], width=3)
        draw.text((15, 2 * height // 3 + 5), "Image Detected",
                  fill=colors['image'], font=font)

    return img_with_boxes


def generate_api_request(api_endpoint, api_key, method, extracted_data,
                         webhook_url, confidence_threshold, output_format):
    """Generate a realistic API request structure."""
    request_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    api_request = {
        "request": {
            "request_id": request_id,
            "timestamp": timestamp,
            "endpoint": api_endpoint,
            "method": method,
            "headers": {
                "Authorization": f"Bearer {api_key[:8]}{'*' * (len(api_key) - 8)}" if api_key else "Bearer ********",
                "Content-Type": "application/json",
            },
            "parameters": {
                "confidence_threshold": confidence_threshold,
                "output_format": output_format,
                "webhook_url": webhook_url if webhook_url else None,
            }
        },
        "response": {
            "status": "success",
            "status_code": 200,
            "request_id": request_id,
            "data": {
                "extracted_fields": extracted_data,
                "metadata": {
                    "total_fields": len(extracted_data),
                    "filled_fields": sum(1 for v in extracted_data.values() if v),
                    "confidence_scores": {
                        field: round(0.85 + (hash(field) % 15) / 100, 2)
                        for field in extracted_data.keys()
                    }
                }
            }
        }
    }

    return api_request


def process_document_for_ui(file, max_new_tokens, max_image_size,
                            enabled_fields,
                            custom_field_1, custom_field_2, custom_field_3,
                            custom_field_4, custom_field_5, custom_field_6,
                            custom_field_7, custom_field_8, custom_field_9,
                            custom_field_10,
                            api_endpoint, api_key, api_method, webhook_url,
                            confidence_threshold, output_format, enable_batch):
    """Orchestrate OCR and post-processing for Gradio output."""

    process_start = time.time()

    if file is None:
        return ("Error: No file provided.", "0:00:00", "", "", "", "", "",
                "", "", "", "", None, "", "", "", "")

    try:
        # Get OCR engine and process
        engine = get_ocr_engine()
        result = engine.process_document(
            file.name,
            max_tokens=max_new_tokens
        )

        if not result.pages or not result.pages[0].success:
            error_msg = result.pages[0].error_message if result.pages else "Unknown error"
            return (f"Error: {error_msg}", "0:00:00", "", "", "", "", "",
                    "", "", "", "", None, "", "", "", "")

        # Parse structured data
        parser = OutputParser()
        parsed = parser.parse(result.total_text)
        converter = FormatConverter()

        # Generate outputs
        ocr_text = result.total_text
        processing_time = result.total_processing_time

        # HTML preview
        ocr_html = ocr_text.replace('\n', '<br>')
        full_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; border-radius: 8px;">
            <h2 style="color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px;">Document Preview</h2>
            <div style="background: white; padding: 15px; border-radius: 5px; margin-top: 15px; line-height: 1.6;">
                {ocr_html}
            </div>
        </div>
        """

        # Tables
        html_tables = converter.get_all_tables_html(parsed)
        csv_tables = []
        for page in parsed.pages:
            csv_tables.extend(page.tables_csv)
        csv_output = "\n\n".join(csv_tables) if csv_tables else "No tables found."

        # Equations
        equations_output = converter.get_all_equations(parsed)

        # Images, watermarks, page numbers
        images_output = []
        watermarks_output = []
        page_numbers_output = []

        for page in parsed.pages:
            for i, desc in enumerate(page.image_descriptions):
                images_output.append(f"Page {page.page_number}, Image {i + 1}: {desc}")
            for i, wm in enumerate(page.watermarks):
                watermarks_output.append(f"Page {page.page_number}, Watermark {i + 1}: {wm}")
            for i, pn in enumerate(page.page_numbers_extracted):
                page_numbers_output.append(f"Page {page.page_number}: {pn}")

        images_str = "\n".join(images_output) if images_output else "No image descriptions found."
        watermarks_str = "\n".join(watermarks_output) if watermarks_output else "No watermarks found."
        page_nums_str = "\n".join(page_numbers_output) if page_numbers_output else "No page numbers found."

        # JSON output using structured processor
        tables_html_list = []
        for page in parsed.pages:
            tables_html_list.extend(page.tables_html)

        structured_processor = get_structured_processor()
        structured_result = structured_processor.process(result.total_text, tables_html_list)
        json_output = json.dumps(structured_result, indent=2)

        # XML output
        xml_output = converter.to_xml(parsed)

        # Bounding box visualization
        bbox_image = None
        if result.processed_images:
            bbox_image = create_bounding_box_visualization(
                result.processed_images[0], ocr_text
            )

        # Field extraction
        custom_fields = [custom_field_1, custom_field_2, custom_field_3,
                         custom_field_4, custom_field_5, custom_field_6,
                         custom_field_7, custom_field_8, custom_field_9,
                         custom_field_10]
        custom_fields = [f.strip() for f in custom_fields if f and f.strip()]

        extractor = FieldExtractor()
        field_results = extractor.extract(ocr_text, enabled_fields, custom_fields)
        api_data = extractor.to_dict(field_results)

        # API v1 request/response
        total_ms = int((time.time() - process_start) * 1000)
        api_request = generate_api_request(
            api_endpoint, api_key, api_method, api_data,
            webhook_url, confidence_threshold, output_format
        )
        api_request["response"]["processing_time_ms"] = total_ms
        api_v1_json = json.dumps(api_request, indent=2)

        # API v2 request/response (structured output format)
        request_id = str(uuid.uuid4())
        api_v2_response = {
            "api_version": "2.0",
            "job_id": request_id,
            "status": "completed",
            "processing_time_ms": total_ms,
            "document": {
                "filename": result.metadata.filename,
                "file_size_mb": result.metadata.file_size_mb,
                "file_type": result.metadata.file_type,
                "total_pages": result.metadata.total_pages
            },
            "result": structured_result
        }
        api_v2_json = json.dumps(api_v2_response, indent=2)

        # Webhook payload using real extracted data
        webhook_payload = {
            "event": "document.processed",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "webhook_url": webhook_url if webhook_url else "https://api.example.com/webhooks/ocr",
            "request_id": request_id,
            "status": "completed",
            "delivery": {
                "attempt": 1,
                "max_attempts": 3,
                "status": "delivered" if webhook_url else "simulated"
            },
            "data": {
                "document_id": request_id,
                "document_type": structured_result['document_type'],
                "language": structured_result['language'],
                "extracted_fields": structured_result['extracted_fields'],
                "line_items": structured_result['line_items'],
                "entities": structured_result['entities'][:10],  # Limit for readability
                "metadata": {
                    "pages": result.metadata.total_pages,
                    "processing_time_ms": total_ms,
                    "confidence": structured_result['confidence']
                }
            },
            "signature": f"sha256={hashlib.sha256(json.dumps(structured_result['extracted_fields']).encode()).hexdigest()[:32]}"
        }
        webhook_json = json.dumps(webhook_payload, indent=2)

        # Statistics
        stats = extractor.get_statistics(field_results)
        stats_output = f"""
Processing Statistics:

Document Information:
- Filename: {result.metadata.filename}
- File Size: {result.metadata.file_size_mb} MB
- File Type: {result.metadata.file_type}
- Total Pages: {result.metadata.total_pages}

Document Classification:
- Document Type: {structured_result['document_type']}
- Classification Confidence: {structured_result['confidence']}
- Language: {structured_result['language']}

Processing Metrics:
- Total Processing Time: {processing_time}
- API Response Time: {total_ms} ms

Extraction Results:
- Total Fields: {stats['total_fields']}
- Fields Found: {stats['fields_found']}
- Fields Empty: {stats['fields_empty']}
- Success Rate: {stats['success_rate']}%
- Entities Extracted: {len(structured_result['entities'])}
- Line Items Found: {len(structured_result['line_items'])}

Content Detection:
- Tables Found: {sum(len(p.tables_html) for p in parsed.pages)}
- Equations Found: {sum(len(p.latex_equations) for p in parsed.pages)}
- Images Found: {sum(len(p.image_descriptions) for p in parsed.pages)}
- Watermarks Found: {sum(len(p.watermarks) for p in parsed.pages)}
"""

        return (ocr_text, processing_time, full_html, html_tables,
                csv_output, equations_output, images_str,
                watermarks_str, page_nums_str, json_output, xml_output,
                bbox_image, api_v1_json, api_v2_json, webhook_json, stats_output)

    except Exception as e:
        return (f"Error: {str(e)}", "0:00:00", "", "", "", "", "",
                "", "", "", "", None, "", "", "", "")


def create_gradio_interface():
    """Create and return the Gradio interface."""

    with gr.Blocks(theme=gr.themes.Default()) as demo:
        gr.Markdown("""
        # 📄 Nanonets-OCR Document Extractor & API Simulator

        **Professional OCR with Real-World API Integration Simulation**

        **Optimized for 16GB VRAM** | Processing time and detailed statistics included
        """)

        # Main tabs for organized UI
        with gr.Tabs():
            # Tab 1: Process & Results
            with gr.TabItem("📤 Process & Results"):
                with gr.Row():
                    with gr.Column(scale=1):
                        file_input = gr.File(
                            label="📁 Upload Document",
                            file_types=["image", ".pdf"],
                            interactive=True
                        )
                        process_button = gr.Button("🚀 Process Document", variant="primary", size="lg")
                        processing_time_display = gr.Textbox(
                            label="Processing Time",
                            interactive=False
                        )

                # Results section
                with gr.Tabs():
                    with gr.TabItem("Statistics"):
                        stats_output = gr.Textbox(label="Processing Statistics", lines=15)

                    with gr.TabItem("API Request/Response"):
                        gr.Markdown("### API v1 Response (Legacy Format)")
                        api_v1_viewer = gr.Code(label="API v1 - Field Extraction", language="json", lines=15)
                        gr.Markdown("### API v2 Response (Structured Output)")
                        api_v2_viewer = gr.Code(label="API v2 - Enhanced Structured", language="json", lines=20)

                    with gr.TabItem("Webhook Payload"):
                        webhook_output = gr.Code(label="Webhook Payload", language="json", lines=15)

                    with gr.TabItem("Full OCR Text"):
                        full_ocr_text = gr.Textbox(label="Extracted Text", lines=20)

                    with gr.TabItem("HTML Preview"):
                        html_preview = gr.HTML(label="Document Preview")

                    with gr.TabItem("Tables (HTML)"):
                        html_tables = gr.HTML(label="Extracted Tables")

                    with gr.TabItem("Tables (CSV)"):
                        csv_tables = gr.Textbox(label="Tables in CSV", lines=12)

                    with gr.TabItem("LaTeX Equations"):
                        latex_equations = gr.Textbox(label="Equations", lines=8)

                    with gr.TabItem("Image Descriptions"):
                        image_descriptions = gr.Textbox(label="Images", lines=5)

                    with gr.TabItem("Watermarks"):
                        watermarks = gr.Textbox(label="Watermarks", lines=5)

                    with gr.TabItem("Page Numbers"):
                        page_numbers = gr.Textbox(label="Page Numbers", lines=5)

                    with gr.TabItem("Bounding Boxes"):
                        bbox_image = gr.Image(label="Detection Visualization", type="pil")

                    with gr.TabItem("JSON Output"):
                        json_output = gr.Code(label="Structured JSON", language="json", lines=20)

                    with gr.TabItem("XML Output"):
                        xml_output = gr.Code(label="Structured XML", language="html", lines=20)

            # Tab 2: Configuration (Settings + API + Webhooks)
            with gr.TabItem("⚙️ Configuration"):
                with gr.Tabs():
                    # General Settings
                    with gr.TabItem("General"):
                        gr.Markdown("### Processing Parameters")
                        with gr.Row():
                            max_tokens_slider = gr.Slider(
                                minimum=500, maximum=6000, step=250, value=2048,
                                label="Max Tokens",
                                info="Maximum tokens for OCR output",
                                interactive=True
                            )
                            max_image_size_slider = gr.Slider(
                                minimum=512, maximum=2048, step=128, value=1536,
                                label="Max Image Size (px)",
                                info="Resize images to this max dimension",
                                interactive=True
                            )
                        with gr.Row():
                            output_format = gr.Dropdown(
                                choices=["JSON", "XML", "CSV"],
                                value="JSON",
                                label="Output Format"
                            )
                            confidence_threshold = gr.Slider(
                                minimum=0.0, maximum=1.0, step=0.05, value=0.75,
                                label="Confidence Threshold",
                                info="Minimum confidence for field extraction"
                            )
                            enable_batch = gr.Checkbox(
                                label="Enable Batch Processing",
                                value=False
                            )

                    # Field Extraction Settings
                    with gr.TabItem("Field Extraction"):
                        gr.Markdown("### Predefined Fields")
                        field_checkboxes = gr.CheckboxGroup(
                            choices=PREDEFINED_FIELDS,
                            label="Select fields to extract",
                            value=PREDEFINED_FIELDS
                        )

                        gr.Markdown("### Custom Fields")
                        with gr.Row():
                            custom_field_1 = gr.Textbox(label="Custom 1", placeholder="e.g., Tax ID")
                            custom_field_2 = gr.Textbox(label="Custom 2", placeholder="e.g., Reference")
                            custom_field_3 = gr.Textbox(label="Custom 3")
                            custom_field_4 = gr.Textbox(label="Custom 4")
                            custom_field_5 = gr.Textbox(label="Custom 5")
                        with gr.Row():
                            custom_field_6 = gr.Textbox(label="Custom 6")
                            custom_field_7 = gr.Textbox(label="Custom 7")
                            custom_field_8 = gr.Textbox(label="Custom 8")
                            custom_field_9 = gr.Textbox(label="Custom 9")
                            custom_field_10 = gr.Textbox(label="Custom 10")

                    # API Configuration
                    with gr.TabItem("API"):
                        gr.Markdown("### API Endpoint")
                        with gr.Row():
                            api_endpoint = gr.Textbox(
                                label="API Endpoint URL",
                                value="https://api.nanonets.com/v1/ocr/extract",
                                info="Target endpoint for OCR requests"
                            )
                            api_method = gr.Dropdown(
                                choices=["POST", "PUT", "PATCH"],
                                value="POST",
                                label="HTTP Method"
                            )
                        gr.Markdown("### Authentication")
                        api_key = gr.Textbox(
                            label="API Key",
                            type="password",
                            value="sk_test_1234567890",
                            info="Your API key for authentication"
                        )

                    # Webhooks
                    with gr.TabItem("Webhooks"):
                        gr.Markdown("### Webhook Configuration")
                        webhook_url = gr.Textbox(
                            label="Webhook URL",
                            value="https://api.example.com/webhooks/ocr",
                            placeholder="https://your-server.com/webhook",
                            info="URL to receive processing callbacks"
                        )
                        gr.Markdown("""
                        **Webhook Events:** `document.processed`, `document.failed`

                        **Payload:** Extracted fields, metadata, processing time, HMAC signature
                        """)

                        gr.Markdown("### Sample Webhook Payload")
                        sample_webhook = {
                            "event": "document.processed",
                            "event_id": "evt_1234567890abcdef",
                            "timestamp": "2024-01-15T10:30:00Z",
                            "webhook_url": "https://api.example.com/webhooks/ocr",
                            "request_id": "req_abcdef1234567890",
                            "status": "completed",
                            "delivery": {
                                "attempt": 1,
                                "max_attempts": 3,
                                "status": "delivered"
                            },
                            "data": {
                                "document_id": "doc_xyz789",
                                "extracted_fields": {
                                    "invoice_number": "INV-2024-001",
                                    "total_amount": "$1,250.00",
                                    "vendor_name": "Acme Corp"
                                },
                                "metadata": {
                                    "pages": 2,
                                    "processing_time_ms": 1523,
                                    "confidence": 0.94
                                }
                            },
                            "signature": "sha256=a1b2c3d4e5f6..."
                        }
                        gr.Code(
                            value=json.dumps(sample_webhook, indent=2),
                            language="json",
                            label="Example Payload",
                            lines=25,
                            interactive=False
                        )

        # Connect button
        process_button.click(
            fn=process_document_for_ui,
            inputs=[
                file_input, max_tokens_slider, max_image_size_slider,
                field_checkboxes,
                custom_field_1, custom_field_2, custom_field_3,
                custom_field_4, custom_field_5, custom_field_6,
                custom_field_7, custom_field_8, custom_field_9,
                custom_field_10,
                api_endpoint, api_key, api_method, webhook_url,
                confidence_threshold, output_format, enable_batch
            ],
            outputs=[
                full_ocr_text, processing_time_display, html_preview,
                html_tables, csv_tables, latex_equations,
                image_descriptions, watermarks, page_numbers,
                json_output, xml_output, bbox_image,
                api_v1_viewer, api_v2_viewer, webhook_output, stats_output
            ]
        )

    return demo


def run_ui(preload_model: bool = True):
    """Run the Gradio interface.

    Args:
        preload_model: If True, initialize model before launching UI.
    """
    if preload_model:
        print("Initializing OCR engine...")
        engine = get_ocr_engine()
        engine.initialize()
        print("OCR engine ready!")

    demo = create_gradio_interface()
    demo.launch(
        server_name=settings.ui.server_name,
        server_port=settings.ui.server_port,
        share=settings.ui.share
    )


if __name__ == "__main__":
    print("=" * 60)
    print("GRADIO UI")
    print("=" * 60)
    print(f"  Starting UI on {settings.ui.server_name}:{settings.ui.server_port}")
    print("=" * 60)

    run_ui(preload_model=True)
