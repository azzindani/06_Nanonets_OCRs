# Nanonets VL OCR API Documentation

Enterprise-grade Vision-Language OCR API for document processing with intelligent field extraction, document classification, and multi-language support.

## Table of Contents

- [Getting Started](#getting-started)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Document Types](#document-types)
- [Usage Examples](#usage-examples)
- [Gradio Web Interface](#gradio-web-interface)
- [Architecture](#architecture)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### Quick Start

```bash
# Clone repository
git clone <repository-url>
cd 06_Nanonets

# Install dependencies
pip install -r requirements.txt

# Run API server
python main.py --mode api

# Or run Gradio UI
python main.py --mode ui
```

### System Requirements

- Python 3.9+
- NVIDIA GPU with 16GB+ VRAM (recommended)
- CUDA 11.8+ (for GPU acceleration)
- 32GB RAM (recommended)

---

## Installation

### Using pip

```bash
pip install -r requirements.txt
```

### Using Docker

```bash
# Build image
docker build -t nanonets-vl .

# Run with GPU support
docker run --gpus all -p 8000:8000 -p 7860:7860 nanonets-vl

# Or use docker-compose
docker-compose up -d
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_NAME` | `nanonets/Nanonets-OCR-s` | HuggingFace model name |
| `MODEL_QUANTIZATION` | `8bit` | Quantization mode (8bit/4bit/none) |
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `8000` | API server port |
| `MAX_TOKENS` | `2048` | Maximum generation tokens |
| `MAX_IMAGE_SIZE` | `1536` | Maximum image dimension |
| `LOG_LEVEL` | `INFO` | Logging level |
| `ENABLE_CACHE` | `false` | Enable Redis caching |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |

---

## Configuration

### config.yaml

```yaml
model:
  name: nanonets/Nanonets-OCR-s
  quantization: 8bit
  max_tokens: 2048
  max_image_size: 1536

api:
  host: 0.0.0.0
  port: 8000
  api_prefix: /api/v1
  rate_limit: 100  # requests per minute
  enable_cors: true

ui:
  server_name: 0.0.0.0
  server_port: 7860
  share: false

cache:
  enable_cache: false
  redis_url: redis://localhost:6379
  default_ttl: 3600
```

---

## API Reference

### Base URL

```
http://localhost:8000/api/v1
```

### Authentication

Include API key in request headers:

```
X-API-Key: your-api-key
```

### Rate Limiting

- Default: 100 requests per minute
- Headers returned:
  - `X-RateLimit-Limit`: Maximum requests
  - `X-RateLimit-Remaining`: Remaining requests

---

### Endpoints

#### Health Check

```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

---

#### Process Document (v1)

```http
POST /api/v1/ocr
```

**Parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `file` | File | required | Document file (PDF/image) |
| `max_tokens` | int | 2048 | Maximum generation tokens |
| `output_format` | string | json | Output format (json/xml) |
| `structured_output` | bool | true | Return enhanced structured output |
| `detect_language` | bool | true | Detect document language |
| `classify_document` | bool | true | Classify document type |

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/ocr \
  -H "X-API-Key: your-key" \
  -F "file=@invoice.pdf" \
  -F "max_tokens=2048"
```

---

#### Process Document (v2 - Enhanced)

```http
POST /api/v1/v2/ocr
```

Returns clean, structured output optimized for downstream processing.

**Parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `file` | File | required | Document file |
| `max_tokens` | int | 2048 | Maximum tokens |
| `webhook_url` | string | null | Webhook callback URL |

**Response:**
```json
{
  "api_version": "2.0",
  "job_id": "uuid",
  "status": "completed",
  "processing_time_ms": 1523,
  "document": {
    "filename": "invoice.pdf",
    "file_size_mb": 0.5,
    "file_type": "PDF",
    "total_pages": 1
  },
  "result": {
    "document_type": "invoice",
    "confidence": 0.85,
    "language": "en",
    "extracted_fields": {
      "invoice_number": "12345",
      "date": "2024-01-15",
      "total": "500.00",
      "bill_to": {
        "name": "John Smith"
      }
    },
    "line_items": [
      {
        "description": "Product A",
        "quantity": "2",
        "rate": "$50.00",
        "amount": "$100.00"
      }
    ],
    "entities": [
      {
        "type": "money",
        "value": "$500.00",
        "confidence": 0.8
      }
    ]
  }
}
```

---

#### Batch Processing

```http
POST /api/v1/ocr/batch
```

Process up to 10 documents in a single request.

**Parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `files` | File[] | required | List of document files |
| `max_tokens` | int | 2048 | Maximum tokens per document |

**Response:**
```json
{
  "batch_id": "uuid",
  "status": "completed",
  "total_files": 3,
  "successful": 3,
  "failed": 0,
  "processing_time_ms": 4500,
  "results": [
    {
      "filename": "doc1.pdf",
      "status": "completed",
      "result": { ... }
    }
  ]
}
```

---

#### Classify Document

```http
POST /api/v1/classify
```

Classify document type without full OCR processing.

**Parameters:**

| Field | Type | Description |
|-------|------|-------------|
| `file` | File | Document file (optional) |
| `text` | string | Text content (optional) |

**Response:**
```json
{
  "document_type": "invoice",
  "confidence": 0.85,
  "all_scores": {
    "invoice": 0.85,
    "receipt": 0.10,
    "contract": 0.05
  },
  "keywords_found": ["invoice", "total", "bill to"]
}
```

---

#### Detect Language

```http
POST /api/v1/detect-language
```

Detect document language.

**Response:**
```json
{
  "primary_language": "en",
  "confidence": 0.95,
  "script_detected": "Latin",
  "is_multilingual": false,
  "secondary_languages": []
}
```

---

#### Extract Entities

```http
POST /api/v1/extract-entities
```

Extract semantic entities from document.

**Response:**
```json
{
  "entities": [
    {"type": "person", "value": "John Smith", "confidence": 0.8},
    {"type": "money", "value": "$500.00", "confidence": 0.8},
    {"type": "date", "value": "01/15/2024", "confidence": 0.8},
    {"type": "email", "value": "john@example.com", "confidence": 0.8}
  ],
  "summary": "Document contains: 1 person(s), 3 monetary value(s)",
  "key_points": []
}
```

---

#### Structured Output

```http
POST /api/v1/structured
```

Get full structured output with all extracted data.

---

## Document Types

The system supports 10 document types with specialized extraction:

### Invoice
- invoice_number, date, total, bill_to, ship_to
- subtotal, discount, tax, shipping
- line_items (from tables)

### Receipt
- receipt_number, store, cashier
- payment_method, total

### Contract
- contract_date, parties, effective_date

### Bank Statement
- account_number, statement_period
- opening_balance, closing_balance
- total_deposits, total_withdrawals

### ID Document
- document_number, full_name
- date_of_birth, expiration_date, address

### Medical Record
- patient_name, patient_id, provider
- diagnosis, visit_date, facility

### Tax Document
- tax_year, form_type, taxpayer_name
- ssn, gross_income, tax_due, refund

### Form
- form_number, applicant information

### Letter
- sender, recipient, date, subject

### Report
- title, author, date, sections

---

## Usage Examples

### Python

```python
import requests

# Process single document
with open('invoice.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/v2/ocr',
        headers={'X-API-Key': 'your-key'},
        files={'file': f},
        data={'max_tokens': 2048}
    )
    result = response.json()
    print(result['result']['extracted_fields'])

# Batch processing
files = [
    ('files', ('doc1.pdf', open('doc1.pdf', 'rb'))),
    ('files', ('doc2.pdf', open('doc2.pdf', 'rb'))),
]
response = requests.post(
    'http://localhost:8000/api/v1/ocr/batch',
    headers={'X-API-Key': 'your-key'},
    files=files
)
```

### JavaScript

```javascript
// Using fetch
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('max_tokens', '2048');

const response = await fetch('http://localhost:8000/api/v1/v2/ocr', {
    method: 'POST',
    headers: {
        'X-API-Key': 'your-key'
    },
    body: formData
});
const result = await response.json();
```

### cURL

```bash
# Basic OCR
curl -X POST http://localhost:8000/api/v1/ocr \
  -H "X-API-Key: your-key" \
  -F "file=@document.pdf"

# API v2 with structured output
curl -X POST http://localhost:8000/api/v1/v2/ocr \
  -H "X-API-Key: your-key" \
  -F "file=@invoice.pdf" \
  -F "max_tokens=2048"

# Classify document
curl -X POST http://localhost:8000/api/v1/classify \
  -H "X-API-Key: your-key" \
  -F "text=Invoice #12345 Total: \$500.00"
```

---

## Gradio Web Interface

Access the web interface at `http://localhost:7860`

### Features

- **Document Upload**: Drag & drop or select files
- **Real-time Processing**: See results immediately
- **Multiple Output Formats**: JSON, XML, CSV, HTML
- **Field Extraction**: Configure predefined and custom fields
- **API Simulation**: View API v1 and v2 response formats
- **Webhook Preview**: See webhook payload structure
- **Statistics**: Processing time, confidence scores, entity counts

### Running the UI

```bash
python main.py --mode ui
```

---

## Architecture

### Core Components

```
core/
├── ocr_engine.py          # Main OCR processing engine
├── document_classifier.py  # Document type classification
├── language_support.py     # Language detection
├── semantic_extractor.py   # Entity extraction
├── structured_output.py    # Unified output processor
├── field_extractor.py      # Field extraction
├── output_parser.py        # HTML/text parsing
└── format_converter.py     # JSON/XML/CSV conversion

api/
├── server.py              # FastAPI application
├── routes/
│   ├── ocr.py            # OCR endpoints
│   ├── health.py         # Health checks
│   └── webhook.py        # Webhook handling
├── middleware/
│   ├── auth.py           # API key authentication
│   └── rate_limit.py     # Rate limiting

services/
├── cache.py              # Redis/memory caching

ui/
└── app.py               # Gradio interface
```

### Processing Pipeline

1. **Input**: Document file (PDF/image)
2. **Preprocessing**: Image resizing, format conversion
3. **OCR**: Vision-language model inference
4. **Parsing**: Extract tables, equations, text
5. **Classification**: Detect document type
6. **Extraction**: Extract fields based on document type
7. **Entity Recognition**: Find persons, dates, money, etc.
8. **Output**: Structured JSON response

---

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Performance tests
pytest tests/performance/ -v
```

### Load Testing

```bash
# Start server first
python main.py --mode api

# Run Locust (in another terminal)
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

### Test Coverage

```bash
pytest --cov=core --cov=api tests/
```

---

## Deployment

### Docker Production

```bash
# Build production image
docker build -t nanonets-vl:prod .

# Run with GPU
docker run -d \
  --gpus all \
  -p 8000:8000 \
  -p 7860:7860 \
  -v $(pwd)/data:/data \
  -e API_KEY=your-production-key \
  -e LOG_LEVEL=WARNING \
  nanonets-vl:prod
```

### Docker Compose (Full Stack)

```bash
# With Redis caching
docker-compose --profile with-cache up -d
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nanonets-vl
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: nanonets-vl
        image: nanonets-vl:prod
        resources:
          limits:
            nvidia.com/gpu: 1
        ports:
        - containerPort: 8000
        env:
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: api-key
```

### Performance Tuning

1. **GPU Memory**: Use 8-bit quantization for 16GB VRAM
2. **Batch Size**: Limit concurrent requests based on GPU memory
3. **Caching**: Enable Redis for repeated document processing
4. **Image Size**: Reduce max_image_size for faster processing

---

## Troubleshooting

### Common Issues

#### CUDA Out of Memory

```
RuntimeError: CUDA out of memory
```

**Solution**: Reduce `max_tokens` or `max_image_size`, or use 4-bit quantization.

#### Model Download Fails

```
OSError: Unable to load model
```

**Solution**: Check internet connection, HuggingFace token, or pre-download model:
```bash
huggingface-cli download nanonets/Nanonets-OCR-s
```

#### Rate Limit Exceeded

```json
{"detail": "Rate limit exceeded. Retry after 60 seconds."}
```

**Solution**: Wait or increase rate limit in config.

#### Redis Connection Failed

```
Redis connection failed: Connection refused
```

**Solution**: Start Redis server or set `ENABLE_CACHE=false`.

### Logging

Enable debug logging:

```bash
LOG_LEVEL=DEBUG python main.py --mode api
```

### Health Checks

```bash
# API health
curl http://localhost:8000/api/v1/health

# Readiness
curl http://localhost:8000/api/v1/ready
```

---

## Support

- **Issues**: https://github.com/anthropics/claude-code/issues
- **Documentation**: `/docs` endpoint for OpenAPI/Swagger
- **API Explorer**: `/redoc` for ReDoc interface

---

## License

MIT License - see LICENSE file for details.
