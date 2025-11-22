# Nanonets OCR API Documentation

## Overview

The Nanonets OCR API provides endpoints for document processing, text extraction, and intelligent field extraction using Vision-Language models.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

API requests require authentication via API key or JWT token.

```bash
# Using API Key
curl -H "X-API-Key: your-api-key" https://api.example.com/api/v1/ocr

# Using JWT Token
curl -H "Authorization: Bearer your-jwt-token" https://api.example.com/api/v1/ocr
```

## Endpoints

### Health Check

#### GET /health

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET /ready

Check if service is ready to accept requests.

**Response:**
```json
{
  "ready": true,
  "services": {
    "database": "connected",
    "model": "loaded"
  }
}
```

### OCR Processing

#### POST /api/v1/ocr

Process a single image for text extraction.

**Request Body:**
```json
{
  "image": "base64-encoded-image-string",
  "options": {
    "language": "en",
    "extract_tables": true,
    "extract_fields": true,
    "document_type": "auto"
  }
}
```

**Response:**
```json
{
  "text": "Extracted text content...",
  "confidence": 0.95,
  "document_type": "invoice",
  "fields": {
    "invoice_number": "INV-2024-001",
    "date": "2024-01-15",
    "total": "$500.00"
  },
  "tables": [...],
  "processing_time_ms": 250
}
```

#### POST /api/v1/ocr/batch

Process multiple images in batch.

**Request Body:**
```json
{
  "images": [
    "base64-image-1",
    "base64-image-2"
  ],
  "options": {
    "parallel": true
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "index": 0,
      "text": "...",
      "confidence": 0.92
    },
    {
      "index": 1,
      "text": "...",
      "confidence": 0.88
    }
  ],
  "total_processing_time_ms": 480
}
```

### Document Classification

#### POST /api/v1/classify

Classify document type.

**Request Body:**
```json
{
  "text": "Invoice content...",
  "image": "optional-base64-image"
}
```

**Response:**
```json
{
  "document_type": "invoice",
  "confidence": 0.95,
  "all_scores": {
    "invoice": 0.95,
    "receipt": 0.3,
    "contract": 0.1
  }
}
```

### Field Extraction

#### POST /api/v1/extract

Extract specific fields from document.

**Request Body:**
```json
{
  "text": "Document content...",
  "schema": {
    "invoice_number": {
      "type": "string",
      "description": "Invoice identification number"
    },
    "total": {
      "type": "money",
      "description": "Total amount due"
    }
  }
}
```

**Response:**
```json
{
  "fields": {
    "invoice_number": {
      "value": "INV-2024-001",
      "confidence": 0.92,
      "location": {"page": 1, "bbox": [100, 50, 200, 70]}
    },
    "total": {
      "value": "$500.00",
      "confidence": 0.88
    }
  }
}
```

### Language Detection

#### POST /api/v1/detect-language

Detect document language.

**Request Body:**
```json
{
  "text": "Text to analyze..."
}
```

**Response:**
```json
{
  "primary_language": "en",
  "confidence": 0.95,
  "is_multilingual": false,
  "secondary_languages": []
}
```

## Supported Document Types

- `invoice` - Invoices and bills
- `receipt` - Purchase receipts
- `contract` - Legal contracts and agreements
- `form` - Application forms
- `letter` - Business letters
- `report` - Reports and analyses
- `id_document` - ID cards, passports
- `bank_statement` - Bank statements
- `tax_document` - Tax forms (W-2, 1099)
- `medical` - Medical records

## Supported Languages

The API supports 25+ languages including:

- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Chinese (zh)
- Japanese (ja)
- Korean (ko)
- Arabic (ar)
- Russian (ru)
- And more...

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid request",
  "message": "Missing required field: image",
  "code": "INVALID_REQUEST"
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing API key",
  "code": "UNAUTHORIZED"
}
```

### 422 Validation Error
```json
{
  "error": "Validation error",
  "details": [
    {"field": "image", "message": "Invalid base64 encoding"}
  ]
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred",
  "request_id": "abc123"
}
```

## Rate Limits

| Plan | Requests/min | Requests/day |
|------|-------------|--------------|
| Free | 10 | 100 |
| Pro | 100 | 10,000 |
| Enterprise | Unlimited | Unlimited |

## SDKs and Examples

### Python

```python
import requests
import base64

def process_document(image_path, api_key):
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()

    response = requests.post(
        'http://localhost:8000/api/v1/ocr',
        json={'image': image_data},
        headers={'X-API-Key': api_key}
    )
    return response.json()
```

### cURL

```bash
curl -X POST http://localhost:8000/api/v1/ocr \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"image": "base64-encoded-image"}'
```

## Webhooks

Configure webhooks for async processing:

```json
{
  "url": "https://your-server.com/webhook",
  "events": ["processing.complete", "processing.failed"],
  "secret": "webhook-secret"
}
```

Webhook payload:
```json
{
  "event": "processing.complete",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "job_id": "job-123",
    "status": "complete",
    "result": {...}
  }
}
```

## Performance Tips

1. **Use batch processing** for multiple documents
2. **Compress images** before sending (JPEG quality 85)
3. **Specify document type** if known to skip classification
4. **Use async webhooks** for large documents

## Changelog

### v1.0.0 (2024-01)
- Initial release
- OCR processing
- Document classification
- Field extraction
- Multi-language support
