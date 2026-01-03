"""
Gradio web interface for document OCR processing via API backend.

This app communicates with the FastAPI backend via HTTP calls instead of 
directly importing core modules. The UI matches the original app.py exactly.
"""
import warnings
# Suppress known compatibility warnings
warnings.filterwarnings("ignore", message=".*MessageFactory.*")
warnings.filterwarnings("ignore", message=".*bcrypt.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)

import gradio as gr
import json
import os
import re
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from ui.api_client import get_api_client, OCRAPIClient


def create_bounding_box_visualization(image: Image.Image, ocr_text: str) -> Image.Image:
    """Create visualization with bounding boxes for detected elements."""
    img_with_boxes = image.copy()
    draw = ImageDraw.Draw(img_with_boxes)

    try:
        # Try common font paths
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc"
        ]
        font = None
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, 14)
                break
        if font is None:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    colors = {
        'table': (255, 0, 0),      # Red
        'equation': (0, 255, 0),    # Green
        'image': (0, 0, 255),       # Blue
        'watermark': (255, 255, 0), # Yellow
        'text': (128, 128, 128),    # Gray
    }

    width, height = img_with_boxes.size
    y_offset = 10

    # Draw indicators for detected elements
    from bs4 import BeautifulSoup

    # Check for tables
    soup = BeautifulSoup(ocr_text, 'html.parser')
    if soup.find_all('table') or '<table' in ocr_text.lower():
        draw.rectangle([(10, y_offset), (width - 10, y_offset + 40)],
                       outline=colors['table'], width=3)
        draw.text((15, y_offset + 5), "📊 Table Detected", fill=colors['table'], font=font)
        y_offset += 50

    # Check for equations (LaTeX style)
    if re.search(r'\$\$[^$]+\$\$|\$[^$]+\$|\\begin\{equation\}', ocr_text):
        draw.rectangle([(10, y_offset), (width - 10, y_offset + 40)],
                       outline=colors['equation'], width=3)
        draw.text((15, y_offset + 5), "🔢 Equation Detected", fill=colors['equation'], font=font)
        y_offset += 50

    # Check for images
    if re.search(r'<img>.*?</img>|\[Image:', ocr_text, re.IGNORECASE):
        draw.rectangle([(10, y_offset), (width - 10, y_offset + 40)],
                       outline=colors['image'], width=3)
        draw.text((15, y_offset + 5), "🖼️ Image Detected", fill=colors['image'], font=font)
        y_offset += 50

    # Check for watermarks
    if re.search(r'watermark|confidential|draft|sample', ocr_text, re.IGNORECASE):
        draw.rectangle([(10, y_offset), (width - 10, y_offset + 40)],
                       outline=colors['watermark'], width=3)
        draw.text((15, y_offset + 5), "💧 Watermark Detected", fill=colors['watermark'], font=font)
        y_offset += 50

    # Draw border around entire document
    draw.rectangle([(2, 2), (width - 2, height - 2)], outline=colors['text'], width=2)

    # Add info text at bottom
    info_text = f"Document: {width}x{height}px | OCR Text: {len(ocr_text):,} chars"
    draw.text((10, height - 25), info_text, fill=colors['text'], font=font)

    return img_with_boxes


# Predefined fields (same as original)
PREDEFINED_FIELDS = [
    "Company Name", "Company Address", "Company Phone", "Company Email", "Company Website",
    "Invoice Number", "Invoice Date", "Due Date", "PO Number", "Reference Number",
    "Bill To Name", "Bill To Address", "Bill To Phone", "Bill To Email",
    "Ship To Name", "Ship To Address", "Ship To Phone", "Ship To Email",
    "Subtotal", "Tax Amount", "Tax Rate", "Discount Amount", "Shipping Cost",
    "Total Amount", "Amount Paid", "Amount Due", "Currency",
    "Payment Terms", "Payment Method", "Bank Name", "Account Number", "SWIFT Code",
    "Item Description", "Item Quantity", "Item Unit Price", "Item Total",
    "Customer ID", "Vendor ID", "Department", "Project Code",
    "Notes", "Terms and Conditions", "Signature", "Date of Signature",
    "Sales Person", "Customer Service Rep", "Approval Status", "Document Type",
    "Purchase Order Number", "Contract Number", "License Number", "Registration Number"
]


def get_sample_documents():
    """Get sample document paths from tests/asset directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    asset_dir = os.path.join(base_dir, "tests", "asset")

    samples = []

    if os.path.exists(asset_dir):
        sample_files = [
            ("invoice1.pdf", "Invoice PDF"),
            ("docparsing_example1.jpg", "Document 1"),
            ("docparsing_example2.jpg", "Document 2"),
            ("ocr_example1.jpg", "OCR Example 1"),
            ("ocr_example2.jpg", "OCR Example 2"),
            ("docparsing_example3.jpg", "Document 3"),
        ]

        for filename, name in sample_files:
            filepath = os.path.join(asset_dir, filename)
            if os.path.exists(filepath):
                samples.append(filepath)

    return samples


def process_document_via_api(
    file,
    max_new_tokens, max_image_size,
    enabled_fields,
    custom_field_1, custom_field_2, custom_field_3,
    custom_field_4, custom_field_5, custom_field_6,
    custom_field_7, custom_field_8, custom_field_9,
    custom_field_10,
    api_endpoint, api_key, api_method, webhook_url,
    confidence_threshold, output_format, enable_batch
):
    """Orchestrate OCR via API and format for Gradio output."""

    if file is None:
        return ("Error: No file provided.", "0:00:00", "", "", "", "", "",
                "", "", "", "", None, "", "", "", "")

    try:
        # Use the configured API endpoint
        client = get_api_client(base_url=api_endpoint, api_key=api_key)
        
        # Check API connection first
        health = client.health_check()
        if not health.success:
            error_msg = f"API Connection Failed: {health.error}"
            return (error_msg, "0:00:00", "", "", "", "", "",
                    "", "", "", "", None, "", "", "", "")

        # Process document via API v2 (structured output)
        result = client.process_document_v2(
            file_path=file.name,
            max_tokens=max_new_tokens,
            webhook_url=webhook_url if webhook_url else None
        )

        if not result.success:
            error_msg = f"Processing Failed: {result.error}"
            return (error_msg, "0:00:00", "", "", "", "", "",
                    "", "", "", "", None, "", "", "", "")

        data = result.data
        
        # Extract data from API response
        processing_time_ms = data.get("processing_time_ms", 0)
        processing_time = f"{processing_time_ms / 1000:.2f}s"
        doc_info = data.get("document", {})
        structured_result = data.get("result", {})

        # OCR text - check multiple possible locations
        raw_data = structured_result.get("raw", {})
        ocr_text = raw_data.get("text", "") or structured_result.get("raw_text", "") or ""
        
        # If still empty, try to get from tables or other sources
        if not ocr_text and raw_data.get("pages"):
            # Combine text from all pages
            page_texts = []
            for page in raw_data.get("pages", []):
                if page.get("text"):
                    page_texts.append(page.get("text", ""))
            ocr_text = "\n\n".join(page_texts)


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

        # Tables HTML - try to use raw HTML tables first, then line items
        raw_tables = raw_data.get("tables_html", [])
        line_items = structured_result.get("line_items", [])
        
        if raw_tables:
            # Use the raw HTML tables from the OCR
            html_tables = "<div style='padding: 10px;'>"
            for i, table in enumerate(raw_tables):
                html_tables += f"<h4>Table {i+1}</h4>{table}<br><br>"
            html_tables += "</div>"
        elif line_items:
            html_tables = "<table border='1' style='border-collapse: collapse; width: 100%;'>"
            html_tables += "<tr style='background: #4CAF50; color: white;'>"
            html_tables += "<th style='padding: 8px;'>Description</th>"
            html_tables += "<th style='padding: 8px;'>Quantity</th>"
            html_tables += "<th style='padding: 8px;'>Unit Price</th>"
            html_tables += "<th style='padding: 8px;'>Total</th></tr>"
            for item in line_items:
                html_tables += f"<tr><td style='padding: 8px;'>{item.get('description', '')}</td>"
                html_tables += f"<td style='padding: 8px; text-align: center;'>{item.get('quantity', '')}</td>"
                html_tables += f"<td style='padding: 8px; text-align: right;'>{item.get('unit_price', '')}</td>"
                html_tables += f"<td style='padding: 8px; text-align: right;'>{item.get('total', '')}</td></tr>"
            html_tables += "</table>"
        else:
            html_tables = "<p>No tables found in document.</p>"

        # CSV tables
        csv_output = "Description,Quantity,Unit Price,Total\n"
        for item in line_items:
            csv_output += f"{item.get('description', '')},{item.get('quantity', '')},{item.get('unit_price', '')},{item.get('total', '')}\n"
        if not line_items:
            csv_output = "No tables found."

        # Extract equations, watermarks, images from pages
        equations_list = []
        watermarks_list = []
        images_list = []
        page_numbers_list = []
        
        for page in raw_data.get("pages", []):
            # Equations (LaTeX)
            if page.get("latex_equations"):
                for eq in page.get("latex_equations", []):
                    equations_list.append(eq)
            # Watermarks
            if page.get("watermarks"):
                for wm in page.get("watermarks", []):
                    watermarks_list.append(f"Page {page.get('page_number', '?')}: {wm}")
            # Image descriptions
            if page.get("image_descriptions"):
                for i, desc in enumerate(page.get("image_descriptions", [])):
                    images_list.append(f"Page {page.get('page_number', '?')}, Image {i+1}: {desc}")
            # Page numbers
            if page.get("page_numbers_extracted"):
                for pn in page.get("page_numbers_extracted", []):
                    page_numbers_list.append(f"Page {page.get('page_number', '?')}: {pn}")

        equations_output = "\n".join(equations_list) if equations_list else "No equations found."
        watermarks_str = "\n".join(watermarks_list) if watermarks_list else "No watermarks detected."
        images_str = "\n".join(images_list) if images_list else "No image descriptions found."
        page_nums_str = "\n".join(page_numbers_list) if page_numbers_list else f"Total Pages: {doc_info.get('total_pages', 1)}"


        # JSON output
        json_output = json.dumps(structured_result, indent=2)

        # XML output (simplified)
        xml_output = f"""<?xml version="1.0" encoding="UTF-8"?>
<document>
    <metadata>
        <filename>{doc_info.get('filename', '')}</filename>
        <file_type>{doc_info.get('file_type', '')}</file_type>
        <total_pages>{doc_info.get('total_pages', 1)}</total_pages>
    </metadata>
    <document_type>{structured_result.get('document_type', '')}</document_type>
    <language>{structured_result.get('language', '')}</language>
    <confidence>{structured_result.get('confidence', 0)}</confidence>
    <extracted_fields>
        {chr(10).join([f'        <field name="{k}">{v}</field>' for k, v in structured_result.get('extracted_fields', {}).items()])}
    </extracted_fields>
</document>"""

        # Bounding box visualization - load the uploaded file
        bbox_image = None
        try:
            file_ext = os.path.splitext(file.name)[1].lower()
            
            if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']:
                # Load image directly
                uploaded_image = Image.open(file.name)
                if uploaded_image.mode != 'RGB':
                    uploaded_image = uploaded_image.convert('RGB')
                bbox_image = create_bounding_box_visualization(uploaded_image, ocr_text)
                
            elif file_ext == '.pdf':
                # Try to extract first page from PDF as image
                try:
                    import fitz  # PyMuPDF
                    pdf_doc = fitz.open(file.name)
                    if len(pdf_doc) > 0:
                        page = pdf_doc[0]
                        # Render at 150 DPI for good quality
                        mat = fitz.Matrix(150/72, 150/72)
                        pix = page.get_pixmap(matrix=mat)
                        # Convert to PIL Image
                        uploaded_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        bbox_image = create_bounding_box_visualization(uploaded_image, ocr_text)
                    pdf_doc.close()
                except ImportError:
                    # PyMuPDF not available, create a placeholder
                    placeholder = Image.new('RGB', (800, 600), color=(245, 245, 245))
                    draw = ImageDraw.Draw(placeholder)
                    draw.text((50, 280), "PDF Preview: Install PyMuPDF for visualization", fill=(100, 100, 100))
                    bbox_image = placeholder
        except Exception as e:
            # If visualization fails, create error placeholder
            placeholder = Image.new('RGB', (800, 100), color=(255, 240, 240))
            draw = ImageDraw.Draw(placeholder)
            draw.text((10, 40), f"Visualization error: {str(e)[:60]}", fill=(200, 0, 0))
            bbox_image = placeholder


        # API v1 request/response (simulated from v2 data)
        api_v1_json = json.dumps({
            "request": {
                "endpoint": api_endpoint,
                "method": api_method,
                "headers": {
                    "Authorization": f"Bearer {api_key[:8]}{'*' * 8}" if api_key else "Bearer ********",
                    "Content-Type": "multipart/form-data",
                },
                "parameters": {
                    "confidence_threshold": confidence_threshold,
                    "output_format": output_format,
                }
            },
            "response": {
                "status": "success",
                "status_code": 200,
                "processing_time_ms": processing_time_ms,
                "extracted_fields": structured_result.get("extracted_fields", {})
            }
        }, indent=2)

        # API v2 response
        api_v2_json = json.dumps(data, indent=2)

        # Webhook payload
        import uuid
        import hashlib
        webhook_payload = {
            "event": "document.processed",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "webhook_url": webhook_url if webhook_url else "https://api.example.com/webhooks/ocr",
            "request_id": data.get("job_id", str(uuid.uuid4())),
            "status": "completed",
            "delivery": {
                "attempt": 1,
                "max_attempts": 3,
                "status": "delivered" if webhook_url else "simulated"
            },
            "data": {
                "document_id": data.get("job_id", ""),
                "document_type": structured_result.get('document_type', ''),
                "language": structured_result.get('language', ''),
                "extracted_fields": structured_result.get('extracted_fields', {}),
                "line_items": line_items[:10],  # Limit for readability
                "entities": structured_result.get('entities', [])[:10],
                "metadata": {
                    "pages": doc_info.get('total_pages', 1),
                    "processing_time_ms": processing_time_ms,
                    "confidence": structured_result.get('confidence', 0)
                }
            },
            "signature": f"sha256={hashlib.sha256(json.dumps(structured_result.get('extracted_fields', {})).encode()).hexdigest()[:32]}"
        }
        webhook_json = json.dumps(webhook_payload, indent=2)

        # Statistics
        extracted_fields = structured_result.get('extracted_fields', {})
        entities = structured_result.get('entities', [])
        
        stats_output = f"""
Processing Statistics:

Document Information:
- Filename: {doc_info.get('filename', 'N/A')}
- File Size: {doc_info.get('file_size_mb', 0):.3f} MB
- File Type: {doc_info.get('file_type', 'N/A')}
- Total Pages: {doc_info.get('total_pages', 1)}

Document Classification:
- Document Type: {structured_result.get('document_type', 'N/A')}
- Classification Confidence: {structured_result.get('confidence', 0):.2f}
- Language: {structured_result.get('language', 'N/A')}

Processing Metrics:
- Total Processing Time: {processing_time}
- API Response Time: {processing_time_ms} ms
- API Version: {data.get('api_version', '2.0')}
- Job ID: {data.get('job_id', 'N/A')}

Extraction Results:
- Total Fields: {len(extracted_fields)}
- Fields Found: {sum(1 for v in extracted_fields.values() if v)}
- Fields Empty: {sum(1 for v in extracted_fields.values() if not v)}
- Entities Extracted: {len(entities)}
- Line Items Found: {len(line_items)}
- Tables Found: {len(raw_tables)}
- Equations Found: {len(equations_list)}
- Watermarks Found: {len(watermarks_list)}
- Images Found: {len(images_list)}

OCR Text:
- Characters: {len(ocr_text):,}
- Words: {len(ocr_text.split()):,}
- Lines: {len(ocr_text.split(chr(10))):,}

API Connection:
- Endpoint: {api_endpoint}
- Status: Connected ✓
"""


        return (ocr_text, processing_time, full_html, html_tables,
                csv_output, equations_output, images_str,
                watermarks_str, page_nums_str, json_output, xml_output,
                bbox_image, api_v1_json, api_v2_json, webhook_json, stats_output)

    except Exception as e:
        import traceback
        error_msg = f"Error: {str(e)}\n\n{traceback.format_exc()}"
        return (error_msg, "0:00:00", "", "", "", "", "",
                "", "", "", "", None, "", "", "", "")


def create_gradio_interface(default_api_url: str = "http://localhost:8000"):
    """Create and return the Gradio interface (matching original app.py)."""

    # Get sample documents
    sample_images = get_sample_documents()

    # Custom CSS to make file upload text smaller
    custom_css = """
    /* Target file upload with custom class */
    .small-upload span,
    .small-upload .upload-button,
    .small-upload button {
        font-size: 9px !important;
    }
    """

    with gr.Blocks(theme=gr.themes.Default(), css=custom_css) as demo:
        gr.Markdown("""
        # Nanonets-OCR Document Extractor & API Simulator

        **Professional OCR with Real-World API Integration** | Running via API Backend
        """)

        # Main tabs for organized UI
        with gr.Tabs():
            # Tab 1: Process & Results
            with gr.TabItem("Process & Results"):
                with gr.Row():
                    with gr.Column(scale=2):
                        file_input = gr.File(
                            label="Upload Document",
                            file_types=["image", ".pdf"],
                            interactive=True,
                            height=118,
                            elem_classes=["small-upload"]
                        )
                    with gr.Column(scale=1):
                        processing_time_display = gr.Textbox(
                            label="Processing Time",
                            interactive=False,
                            lines=1
                        )
                        process_button = gr.Button("Process Document", variant="primary", size="lg")

                # Sample documents
                if sample_images:
                    gr.Markdown("**Sample Documents** - Click to load:")
                    gr.Examples(
                        examples=[[path] for path in sample_images],
                        inputs=[file_input],
                        examples_per_page=6,
                        label="Sample Documents"
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
                        gr.Markdown("> **Note:** This UI connects to a real API backend. Configure the endpoint below.")
                        with gr.Row():
                            api_endpoint = gr.Textbox(
                                label="API Endpoint URL",
                                value=default_api_url,
                                info="FastAPI backend server URL"
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
                            value="",
                            info="Your API key for authentication (leave empty if not required)"
                        )
                        
                        # Connection test
                        gr.Markdown("### Connection Test")
                        with gr.Row():
                            test_connection_btn = gr.Button("🔍 Test Connection", size="sm")
                            connection_status = gr.Textbox(label="Status", lines=3, interactive=False)
                        
                        def test_connection(url, key):
                            try:
                                client = get_api_client(base_url=url, api_key=key)
                                result = client.health_check()
                                if result.success:
                                    data = result.data
                                    return f"✅ Connected!\nModel: {data.get('model_loaded', False)}\nGPU: {data.get('gpu_available', False)}"
                                else:
                                    return f"❌ Failed: {result.error}"
                            except Exception as e:
                                return f"❌ Error: {str(e)}"
                        
                        test_connection_btn.click(
                            fn=test_connection,
                            inputs=[api_endpoint, api_key],
                            outputs=[connection_status]
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
            fn=process_document_via_api,
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


def run_api_ui(
    api_url: str = "http://localhost:8000",
    server_name: str = "0.0.0.0",
    server_port: int = 7861,
    share: bool = False
):
    """
    Run the API-based Gradio interface.
    
    Args:
        api_url: Default API server URL
        server_name: Gradio server name
        server_port: Gradio server port
        share: Whether to create a public link
    """
    print("=" * 60)
    print("GRADIO API UI")
    print("=" * 60)
    print(f"  API URL: {api_url}")
    print(f"  UI URL: http://{server_name}:{server_port}")
    print("=" * 60)
    
    # Check API connection on startup
    client = get_api_client(base_url=api_url)
    health = client.health_check()
    if health.success:
        print("  ✓ API server is accessible")
        data = health.data
        print(f"  ✓ Model loaded: {data.get('model_loaded', False)}")
        print(f"  ✓ GPU available: {data.get('gpu_available', False)}")
    else:
        print(f"  ⚠ API server not responding: {health.error}")
        print("  Make sure to start the API server: python -m api.server")
    print("=" * 60)
    
    demo = create_gradio_interface(default_api_url=api_url)
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        share=share
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run OCR API Client UI")
    parser.add_argument(
        "--api-url", 
        default="http://localhost:8000",
        help="API server URL"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=7861,
        help="UI server port"
    )
    parser.add_argument(
        "--share", 
        action="store_true",
        help="Create public link"
    )
    
    args = parser.parse_args()
    
    run_api_ui(
        api_url=args.api_url,
        server_port=args.port,
        share=args.share
    )
