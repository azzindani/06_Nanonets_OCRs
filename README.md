# Nanonets VL - Production OCR & Document Extraction System

Enterprise-grade Vision-Language OCR system for intelligent document processing, table extraction, and structured data output.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GRADIO UI LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │
│  │   Upload    │  │  Settings   │  │   Output    │  │ API Config │  │
│  │   Panel     │  │   Panel     │  │   Tabs      │  │   Panel    │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘  │
└─────────┼────────────────┼────────────────┼────────────────┼────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API LAYER                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │  REST Endpoints │  │  Request Queue  │  │  Response Handler   │  │
│  │  /ocr, /health  │  │  (Async Jobs)   │  │  (JSON/XML/CSV)     │  │
│  └────────┬────────┘  └────────┬────────┘  └──────────┬──────────┘  │
└───────────┼────────────────────┼─────────────────────┼──────────────┘
            │                    │                     │
            ▼                    ▼                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PROCESSING LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────┐  │
│  │   Document   │  │    OCR       │  │   Output     │  │  Field  │  │
│  │   Processor  │  │   Engine     │  │   Parser     │  │ Extract │  │
│  │  (PDF/Image) │  │  (VL Model)  │  │  (Structure) │  │         │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────┬────┘  │
└─────────┼─────────────────┼─────────────────┼───────────────┼───────┘
          │                 │                 │               │
          ▼                 ▼                 ▼               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     INFRASTRUCTURE LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────┐  │
│  │   Hardware   │  │    Model     │  │    Cache     │  │  Logger │  │
│  │   Detection  │  │   Manager    │  │   (Redis)    │  │  Utils  │  │
│  │  (GPU/CPU)   │  │  (HF Models) │  │              │  │         │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Input (PDF/Image)
       │
       ▼
┌─────────────────┐
│ File Validation │ ← Supported formats: JPG, PNG, PDF, TIFF, BMP, GIF
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Pre-processing  │ ← Resize, normalize, PDF page extraction
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Model Inference│ ← Nanonets-OCR-s or Nanonets-OCR2-3B
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Output Parsing  │ ← Extract tables, equations, images, watermarks
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Field Extraction│ ← 50+ predefined + custom fields
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Format Output   │ ← JSON, XML, CSV, HTML, PDF
└────────┬────────┘
         │
         ▼
    Response/Webhook
```

---

## Features by Priority

### MVP (Minimum Viable Product)

Required for first deployment:

- [x] **Core OCR Engine**
  - [x] Model loading with hardware detection
  - [x] Single image processing
  - [x] Multi-page PDF processing
  - [x] Memory optimization (8-bit quantization)

- [x] **Basic API**
  - [x] POST /api/v1/ocr - Process document
  - [x] GET /api/v1/health - Health check
  - [x] Basic authentication (API key)

- [x] **Output Formats**
  - [x] Raw text extraction
  - [x] JSON structured output
  - [x] Table extraction (HTML/CSV)

- [x] **Gradio UI**
  - [x] Document upload
  - [x] Processing settings
  - [x] Result display tabs

- [x] **Configuration**
  - [x] Environment variables
  - [x] Model selection
  - [x] Hardware settings

### Phase 1: Production Ready

- [x] **Enhanced API**
  - [x] Request queue (async processing)
  - [x] Rate limiting
  - [x] Webhook callbacks
  - [x] Multiple output formats (XML, CSV, PDF)

- [x] **Field Extraction**
  - [x] 50+ predefined invoice fields
  - [x] Custom field configuration
  - [x] Confidence scoring

- [x] **Testing & CI/CD**
  - [x] Unit tests (all components)
  - [x] Integration tests
  - [x] GitHub Actions pipeline
  - [x] Code coverage > 80%

- [x] **Deployment**
  - [x] Docker containerization
  - [x] docker-compose setup
  - [x] Environment documentation

- [x] **Monitoring**
  - [x] Structured logging
  - [x] Processing metrics
  - [x] Error tracking

### Phase 2: Enhanced Features

- [x] **Advanced Processing**
  - [x] Batch document processing
  - [x] Multi-model support (switch between OCR-s and OCR2-3B)
  - [x] Result caching (Redis)
  - [x] Concurrent request handling

- [x] **Enhanced UI**
  - [x] Job history & tracking
  - [x] Analytics dashboard
  - [x] Field configuration UI
  - [x] API testing interface

- [x] **Security**
  - [x] JWT authentication
  - [x] Role-based access control
  - [x] Audit logging
  - [x] Input sanitization

### Phase 3: Enterprise Scale

- [ ] **Scalability**
  - [ ] Kubernetes deployment
  - [ ] Horizontal scaling (multiple workers)
  - [ ] Load balancing
  - [ ] GPU cluster support

- [ ] **Advanced Analytics**
  - [ ] Processing statistics
  - [ ] Model performance metrics
  - [ ] Usage analytics
  - [ ] Cost tracking

- [ ] **Enterprise Features**
  - [ ] Multi-tenant support
  - [ ] Custom model training interface
  - [ ] SLA monitoring
  - [ ] Backup & recovery

---

## Directory Structure

```
nanonets-vl/
├── config.py                    # Central configuration
├── main.py                      # Application entry point
├── run_ui.py                    # Gradio UI launcher
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container definition
├── docker-compose.yml           # Multi-service orchestration
├── .env.example                 # Environment template
├── README.md                    # This file
├── DOCUMENTATION.md             # API documentation
├── WORKFLOW.md                  # Development workflow
│
├── core/                        # Business logic
│   ├── __init__.py
│   ├── ocr_engine.py           # Main OCR processing
│   ├── document_processor.py   # PDF/Image handling
│   ├── document_classifier.py  # Document type classification
│   ├── language_support.py     # Language detection
│   ├── semantic_extractor.py   # Entity extraction
│   ├── structured_output.py    # Unified structured output
│   ├── output_parser.py        # Structure extraction
│   ├── field_extractor.py      # Field extraction logic
│   ├── format_converter.py     # Output format conversion
│   ├── format_support.py       # Format utilities
│   ├── schema_extractor.py     # Schema-based extraction
│   └── test_complete_ocr.py    # OCR test module
│
├── models/                      # Model management
│   ├── __init__.py
│   ├── model_manager.py        # Model loading/caching
│   └── hardware_detection.py   # GPU/CPU detection
│
├── api/                         # REST API
│   ├── __init__.py
│   ├── server.py               # FastAPI application
│   ├── test_api.py             # API test module
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── ocr.py              # OCR endpoints (v1, v2, batch)
│   │   ├── health.py           # Health checks
│   │   ├── auth.py             # Auth endpoints
│   │   └── webhook.py          # Webhook handlers
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py             # API key authentication
│   │   └── rate_limit.py       # Rate limiting
│   └── schemas/
│       ├── __init__.py
│       ├── request.py          # Request models
│       └── response.py         # Response models
│
├── ui/                          # Gradio interface
│   ├── __init__.py
│   ├── app.py                  # Main Gradio app
│   ├── components/
│   │   └── __init__.py
│   └── handlers/
│       └── __init__.py
│
├── services/                    # Shared services
│   ├── __init__.py
│   ├── auth.py                 # JWT authentication
│   ├── cache.py                # Redis/memory caching
│   ├── queue.py                # Job queue
│   ├── storage.py              # File storage
│   ├── s3_storage.py           # S3 storage
│   ├── workflow.py             # Workflow engine
│   ├── celery_app.py           # Celery configuration
│   ├── tasks.py                # Background tasks
│   ├── test_services.py        # Services test module
│   └── notifications/          # Notification services
│       ├── __init__.py
│       ├── base.py
│       ├── email.py
│       └── slack.py
│
├── db/                          # Database
│   ├── __init__.py
│   ├── models.py               # SQLAlchemy models
│   ├── session.py              # Database session
│   └── migrations/
│       └── env.py              # Alembic migrations
│
├── integrations/                # External integrations
│   ├── __init__.py
│   └── connectors.py           # Third-party connectors
│
├── utils/                       # Utilities
│   ├── __init__.py
│   ├── logger.py               # Logging configuration
│   ├── validators.py           # Input validation
│   └── startup.py              # Startup utilities
│
└── tests/                       # Test suite
    ├── __init__.py
    ├── conftest.py             # Pytest fixtures
    ├── test_with_assets.py     # Asset-based tests
    ├── asset/                  # Sample documents
    │   ├── invoice1.pdf - invoice9.pdf
    │   ├── docparsing_example1-8.*
    │   └── ocr_example1-6.jpg
    ├── unit/                   # Unit tests
    │   ├── __init__.py
    │   ├── test_document_classifier.py
    │   ├── test_document_processor.py
    │   ├── test_field_extractor.py
    │   ├── test_language_support.py
    │   ├── test_output_parser.py
    │   ├── test_semantic_extractor.py
    │   ├── test_structured_output.py
    │   └── test_validators.py
    ├── integration/            # Integration tests
    │   ├── __init__.py
    │   ├── test_api_endpoints.py
    │   ├── test_api_integration.py
    │   ├── test_api_v2.py
    │   └── test_full_pipeline.py
    └── performance/            # Performance tests
        ├── __init__.py
        ├── benchmark.py
        └── locustfile.py
```

---

## Component Specifications

### Core Components

#### 1. OCR Engine (`core/ocr_engine.py`)

**Purpose**: Main inference engine for document OCR

**Key Functions**:
```python
class OCREngine:
    def __init__(self, model_name: str, config: OCRConfig)
    def process_image(self, image: PIL.Image) -> OCRResult
    def process_pdf(self, pdf_path: str) -> List[OCRResult]
    def get_model_info(self) -> ModelInfo
```

**Tests**:
- `test_process_single_image`: Verify text extraction from image
- `test_process_multipage_pdf`: Verify PDF page processing
- `test_memory_optimization`: Verify memory stays within limits
- `test_model_switching`: Verify switching between OCR-s and OCR2-3B

---

#### 2. Document Processor (`core/document_processor.py`)

**Purpose**: Handle file input, validation, and preprocessing

**Key Functions**:
```python
class DocumentProcessor:
    def validate_file(self, file_path: str) -> ValidationResult
    def preprocess_image(self, image: PIL.Image, max_size: int) -> PIL.Image
    def extract_pdf_pages(self, pdf_path: str) -> List[PIL.Image]
    def get_file_metadata(self, file_path: str) -> FileMetadata
```

**Tests**:
- `test_validate_supported_formats`: Accept JPG, PNG, PDF, etc.
- `test_reject_unsupported_formats`: Reject invalid files
- `test_image_resizing`: Verify resize preserves aspect ratio
- `test_pdf_extraction`: Verify all pages extracted

---

#### 3. Output Parser (`core/output_parser.py`)

**Purpose**: Parse raw OCR output into structured components

**Key Functions**:
```python
class OutputParser:
    def parse(self, raw_output: str) -> ParsedOutput
    def extract_tables(self, content: str) -> List[Table]
    def extract_equations(self, content: str) -> List[str]  # LaTeX
    def extract_images(self, content: str) -> List[ImageCaption]
    def extract_checkboxes(self, content: str) -> List[Checkbox]
```

**Tests**:
- `test_table_extraction`: Verify HTML table parsing
- `test_equation_extraction`: Verify LaTeX equation detection
- `test_checkbox_detection`: Verify filled/unfilled detection
- `test_watermark_detection`: Verify watermark identification

---

#### 4. Field Extractor (`core/field_extractor.py`)

**Purpose**: Extract specific fields from OCR text

**Key Functions**:
```python
class FieldExtractor:
    def __init__(self, field_config: List[FieldDefinition])
    def extract(self, text: str) -> Dict[str, FieldResult]
    def add_custom_field(self, field: FieldDefinition)
    def get_confidence_scores(self) -> Dict[str, float]
```

**Predefined Fields** (50+):
- Company: name, address, phone, email, website
- Invoice: number, date, due_date, po_number
- Addresses: billing, shipping
- Financial: subtotal, tax, discount, total
- Payment: terms, method, bank_details
- Items: description, quantity, unit_price, amount

**Tests**:
- `test_extract_invoice_fields`: Verify all invoice fields
- `test_custom_field_extraction`: Verify custom field support
- `test_confidence_scoring`: Verify confidence calculation
- `test_missing_field_handling`: Verify graceful handling

---

#### 5. Format Converter (`core/format_converter.py`)

**Purpose**: Convert parsed output to various formats

**Key Functions**:
```python
class FormatConverter:
    def to_json(self, parsed: ParsedOutput) -> str
    def to_xml(self, parsed: ParsedOutput) -> str
    def to_csv(self, tables: List[Table]) -> str
    def to_html(self, parsed: ParsedOutput) -> str
    def to_pdf(self, parsed: ParsedOutput) -> bytes
```

**Tests**:
- `test_json_output`: Verify valid JSON structure
- `test_xml_output`: Verify valid XML with schema
- `test_csv_tables`: Verify table CSV export
- `test_html_formatting`: Verify HTML rendering

---

### Model Components

#### 6. Model Manager (`models/model_manager.py`)

**Purpose**: Load, cache, and manage VL models

**Key Functions**:
```python
class ModelManager:
    def __init__(self, config: ModelConfig)
    def load_model(self, model_name: str) -> Model
    def unload_model(self)
    def get_available_models(self) -> List[str]
    def get_model_status(self) -> ModelStatus
```

**Supported Models**:
- `nanonets/nanonets-ocr-s` - Small, fast model
- `nanonets/nanonets-ocr2-3b` - Large, accurate model

**Tests**:
- `test_model_loading`: Verify model loads correctly
- `test_quantization`: Verify 8-bit loading works
- `test_device_placement`: Verify GPU/CPU placement
- `test_model_caching`: Verify model stays loaded

---

#### 7. Hardware Detection (`models/hardware_detection.py`)

**Purpose**: Detect and configure hardware resources

**Key Functions**:
```python
@dataclass
class HardwareConfig:
    device: str              # 'cuda:0', 'cpu'
    gpu_memory: int          # Available VRAM in GB
    quantization: str        # 'none', '8bit'
    max_batch_size: int

def detect_hardware() -> HardwareConfig
def optimize_for_hardware(config: HardwareConfig) -> ModelConfig
```

**Tests**:
- `test_gpu_detection`: Verify CUDA detection
- `test_memory_calculation`: Verify VRAM calculation
- `test_cpu_fallback`: Verify CPU mode works
- `test_quantization_decision`: Verify auto-quantization

---

### API Components

#### 8. API Server (`api/server.py`)

**Purpose**: FastAPI application with REST endpoints

**Endpoints**:
```
POST /api/v1/ocr              - Process document (v1)
POST /api/v1/v2/ocr           - Process document (v2 - enhanced)
POST /api/v1/ocr/batch        - Batch process documents
POST /api/v1/classify         - Classify document type
POST /api/v1/detect-language  - Detect document language
POST /api/v1/extract-entities - Extract named entities
POST /api/v1/structured       - Get structured output
GET  /api/v1/health           - Health check
GET  /api/v1/info             - API information
POST /api/v1/webhook/register - Register webhook
```

**Tests**:
- `test_ocr_endpoint`: Verify document processing
- `test_health_endpoint`: Verify health response
- `test_authentication`: Verify API key validation
- `test_rate_limiting`: Verify rate limit enforcement

---

### UI Components

#### 9. Gradio App (`ui/app.py`)

**Purpose**: Web interface for document processing

**Tabs**:
1. **Upload & Process** - File upload, settings
2. **Raw Output** - Unprocessed OCR text
3. **Structured Text** - Parsed content
4. **Tables** - Extracted tables (HTML/CSV)
5. **Equations** - LaTeX equations
6. **Fields** - Extracted field values
7. **JSON Output** - Full JSON response
8. **XML Output** - Full XML response
9. **API Request** - Generated API call
10. **Statistics** - Processing metrics

**Tests**:
- `test_file_upload`: Verify upload handling
- `test_processing_flow`: Verify end-to-end UI flow
- `test_output_tabs`: Verify all tabs render
- `test_settings_persistence`: Verify settings save

---

## Testing Strategy

### Test Categories

```python
# Unit tests - Fast, no GPU required
@pytest.mark.unit
def test_function():
    pass

# Integration tests - Requires model/GPU
@pytest.mark.integration
def test_pipeline():
    pass

# Slow tests - Long running
@pytest.mark.slow
def test_large_document():
    pass
```

### Test Coverage Requirements

| Component | Minimum Coverage |
|-----------|-----------------|
| core/ | 90% |
| models/ | 85% |
| api/ | 90% |
| ui/ | 70% |
| utils/ | 95% |

### Running Tests

```bash
# Unit tests only (CI)
pytest -m unit -v

# Integration tests (requires GPU)
pytest -m integration -v

# All tests with coverage
pytest --cov=. --cov-report=html --cov-fail-under=80

# Specific component
pytest tests/unit/test_ocr_engine.py -v

# Run module directly
python -m core.ocr_engine
```

### Test Fixtures

```python
# conftest.py
@pytest.fixture
def sample_image():
    return Image.open("tests/fixtures/sample_image.png")

@pytest.fixture
def sample_pdf():
    return "tests/fixtures/sample_invoice.pdf"

@pytest.fixture
def mock_model():
    # Lightweight mock for unit tests
    return MockOCRModel()

@pytest.fixture
def ocr_engine(mock_model):
    return OCREngine(model=mock_model)
```

---

## Development Roadmap

### Sprint 1: Foundation ✅

**Goal**: Basic project structure and core OCR working

- [x] Set up project structure
- [x] Implement `config.py` with all settings
- [x] Port `core/ocr_engine.py` from notebook
- [x] Port `core/document_processor.py`
- [x] Port `models/model_manager.py`
- [x] Port `models/hardware_detection.py`
- [x] Basic unit tests for above
- [x] Verify model loads and processes single image

**Milestone**: `python -m core.ocr_engine` processes test image ✅

---

### Sprint 2: Processing Pipeline ✅

**Goal**: Complete processing pipeline

- [x] Implement `core/output_parser.py`
- [x] Implement `core/field_extractor.py`
- [x] Implement `core/format_converter.py`
- [x] Implement `utils/` modules
- [x] Unit tests for all core components
- [x] Integration test for full pipeline

**Milestone**: End-to-end document processing works ✅

---

### Sprint 3: API Layer ✅

**Goal**: REST API with authentication

- [x] Implement `api/server.py` (FastAPI)
- [x] Implement `api/routes/ocr.py`
- [x] Implement `api/routes/health.py`
- [x] Implement `api/middleware/auth.py`
- [x] Implement `api/schemas/`
- [x] API unit tests
- [x] API integration tests

**Milestone**: `curl` can process documents via API ✅

---

### Sprint 4: Gradio UI ✅

**Goal**: Full Gradio interface

- [x] Implement `ui/app.py`
- [x] Implement all UI components
- [x] Connect UI to processing pipeline
- [x] UI tests
- [x] Documentation

**Milestone**: Gradio UI fully functional ✅

---

### Sprint 5: Production Deployment ✅

**Goal**: Docker deployment ready

- [x] Create `Dockerfile`
- [x] Create `docker-compose.yml`
- [x] GitHub Actions CI/CD
- [x] Environment documentation
- [x] Performance benchmarks
- [x] Security review

**Milestone**: `docker-compose up` runs full system ✅

---

### Sprint 6: Enhanced Features ✅

**Goal**: Production enhancements

- [x] Redis caching
- [x] Job queue (async processing)
- [x] Webhook support
- [x] Rate limiting
- [x] Monitoring & logging
- [x] Load testing

**Milestone**: Production-ready system ✅

---

## Configuration

### Environment Variables

```bash
# .env.example

# Model Configuration
MODEL_NAME=nanonets/nanonets-ocr-s
MODEL_QUANTIZATION=8bit
MAX_IMAGE_SIZE=1536
MAX_TOKENS=2048

# Hardware
DEVICE=auto                    # auto, cuda:0, cpu
GPU_MEMORY_FRACTION=0.9

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=your-secret-key
RATE_LIMIT=100                 # requests per minute

# UI Configuration
GRADIO_SERVER_NAME=0.0.0.0
GRADIO_SERVER_PORT=7860
GRADIO_SHARE=false

# Cache & Storage
REDIS_URL=redis://localhost:6379
STORAGE_PATH=/data/documents

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Config Class

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Model
    model_name: str = "nanonets/nanonets-ocr-s"
    model_quantization: str = "8bit"
    max_image_size: int = 1536
    max_tokens: int = 2048

    # Hardware
    device: str = "auto"
    gpu_memory_fraction: float = 0.9

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_key: str = ""
    rate_limit: int = 100

    # UI
    gradio_server_name: str = "0.0.0.0"
    gradio_server_port: int = 7860

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Hardware Requirements

### Minimum (CPU Mode)
- CPU: 4 cores
- RAM: 16 GB
- Storage: 20 GB
- Processing: ~30-60 seconds per page

### Recommended (GPU Mode)
- CPU: 8 cores
- RAM: 32 GB
- GPU: NVIDIA with 8+ GB VRAM (RTX 3070+)
- Storage: 50 GB SSD
- Processing: ~2-5 seconds per page

### Production (High Volume)
- CPU: 16+ cores
- RAM: 64 GB
- GPU: NVIDIA A10/A100 or RTX 4090
- Storage: 200 GB NVMe SSD
- Processing: <1 second per page

---

## Deployment

### Docker

```dockerfile
# Dockerfile
FROM nvidia/cuda:11.8-runtime-ubuntu22.04

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000 7860

CMD ["python", "main.py"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  nanonets-vl:
    build: .
    ports:
      - "8000:8000"   # API
      - "7860:7860"   # Gradio
    volumes:
      - ./data:/data
    environment:
      - MODEL_NAME=nanonets/nanonets-ocr-s
      - DEVICE=auto
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### Running

```bash
# Development
python main.py

# With Gradio UI only
python ui/app.py

# With API only
python api/server.py

# Docker
docker-compose up -d

# Check health
curl http://localhost:8000/api/v1/health
```

---

## API Documentation

### Process Document

```bash
POST /api/v1/ocr
Content-Type: multipart/form-data
X-API-Key: your-api-key

# Request
file: <document.pdf>
output_format: json
extract_fields: true
max_tokens: 2048

# Response
{
  "job_id": "uuid",
  "status": "completed",
  "processing_time": 2.34,
  "result": {
    "text": "...",
    "tables": [...],
    "fields": {...},
    "metadata": {...}
  }
}
```

### Health Check

```bash
GET /api/v1/health

# Response
{
  "status": "healthy",
  "model_loaded": true,
  "gpu_available": true,
  "version": "1.0.0"
}
```

---

## Contributing

1. Create feature branch: `git checkout -b claude/<feature>-<session-id>`
2. Follow WORKFLOW.md guidelines
3. Write tests for new features
4. Ensure CI passes: `pytest -m unit -v`
5. Submit PR with description

---

## Future Roadmap

See [FUTURE_ROADMAP.md](FUTURE_ROADMAP.md) for detailed plans.

### Upcoming Features

**Phase 5: AI-Native Features**
- Document classification & auto-routing
- Semantic field extraction with LLM
- Handwriting recognition
- Multi-language support (50+ languages)

**Phase 6: Enterprise Intelligence**
- Advanced analytics dashboard
- Visual workflow builder
- 100+ integration connectors
- PII detection & GDPR compliance

**Phase 7: Scale & Performance**
- Edge deployment & offline processing
- TensorRT/ONNX optimization
- 10,000+ documents/hour throughput
- Multi-region global deployment

**Phase 8: Platform Ecosystem**
- SDKs (Python, JS, Java, Go)
- GraphQL & gRPC APIs
- Model marketplace
- White-label solution

### Test Coverage Status

| Component | Status |
|-----------|--------|
| Core OCR | ✅ Tested |
| Document Processor | ✅ Tested |
| Output Parser | ✅ Tested |
| Field Extractor | ✅ Tested |
| API Endpoints | ✅ Tested |
| Auth Service | ✅ Tested |
| Workflow Engine | ✅ Tested |
| Schema Extractor | ✅ Tested |
| Storage Service | ✅ Tested |
| Health Routes | ✅ Tested |
| Notifications | ✅ Tested |
| Connectors | ✅ Tested |

Run tests: `python -m pytest tests/ -v`

---

## License

[Add License]

---

## References

- Original notebooks: `nanonets-nanonets-ocr-s-imp-v6.ipynb`, `nanonets-nanonets-ocr2-3b-imp-v1.ipynb`
- Hugging Face Models: [Nanonets OCR Models](https://huggingface.co/nanonets)
- Development Workflow: `WORKFLOW.md`
