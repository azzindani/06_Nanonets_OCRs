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

- [ ] **Core OCR Engine**
  - [ ] Model loading with hardware detection
  - [ ] Single image processing
  - [ ] Multi-page PDF processing
  - [ ] Memory optimization (8-bit quantization)

- [ ] **Basic API**
  - [ ] POST /api/v1/ocr - Process document
  - [ ] GET /api/v1/health - Health check
  - [ ] Basic authentication (API key)

- [ ] **Output Formats**
  - [ ] Raw text extraction
  - [ ] JSON structured output
  - [ ] Table extraction (HTML/CSV)

- [ ] **Gradio UI**
  - [ ] Document upload
  - [ ] Processing settings
  - [ ] Result display tabs

- [ ] **Configuration**
  - [ ] Environment variables
  - [ ] Model selection
  - [ ] Hardware settings

### Phase 1: Production Ready

- [ ] **Enhanced API**
  - [ ] Request queue (async processing)
  - [ ] Rate limiting
  - [ ] Webhook callbacks
  - [ ] Multiple output formats (XML, CSV, PDF)

- [ ] **Field Extraction**
  - [ ] 50+ predefined invoice fields
  - [ ] Custom field configuration
  - [ ] Confidence scoring

- [ ] **Testing & CI/CD**
  - [ ] Unit tests (all components)
  - [ ] Integration tests
  - [ ] GitHub Actions pipeline
  - [ ] Code coverage > 80%

- [ ] **Deployment**
  - [ ] Docker containerization
  - [ ] docker-compose setup
  - [ ] Environment documentation

- [ ] **Monitoring**
  - [ ] Structured logging
  - [ ] Processing metrics
  - [ ] Error tracking

### Phase 2: Enhanced Features

- [ ] **Advanced Processing**
  - [ ] Batch document processing
  - [ ] Multi-model support (switch between OCR-s and OCR2-3B)
  - [ ] Result caching (Redis)
  - [ ] Concurrent request handling

- [ ] **Enhanced UI**
  - [ ] Job history & tracking
  - [ ] Analytics dashboard
  - [ ] Field configuration UI
  - [ ] API testing interface

- [ ] **Security**
  - [ ] JWT authentication
  - [ ] Role-based access control
  - [ ] Audit logging
  - [ ] Input sanitization

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
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Development dependencies
├── Dockerfile                   # Container definition
├── docker-compose.yml           # Multi-service orchestration
├── .env.example                 # Environment template
├── README.md                    # This file
├── WORKFLOW.md                  # Development workflow
│
├── core/                        # Business logic
│   ├── __init__.py
│   ├── ocr_engine.py           # Main OCR processing
│   ├── document_processor.py   # PDF/Image handling
│   ├── output_parser.py        # Structure extraction
│   ├── field_extractor.py      # Field extraction logic
│   └── format_converter.py     # Output format conversion
│
├── models/                      # Model management
│   ├── __init__.py
│   ├── model_manager.py        # Model loading/caching
│   ├── hardware_detection.py   # GPU/CPU detection
│   └── quantization.py         # 8-bit quantization utils
│
├── api/                         # REST API
│   ├── __init__.py
│   ├── server.py               # FastAPI application
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── ocr.py              # OCR endpoints
│   │   ├── health.py           # Health checks
│   │   └── webhook.py          # Webhook handlers
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication
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
│   │   ├── __init__.py
│   │   ├── upload.py           # Upload component
│   │   ├── settings.py         # Settings panel
│   │   ├── output_tabs.py      # Output display
│   │   └── api_config.py       # API configuration
│   └── handlers/
│       ├── __init__.py
│       └── process.py          # Processing handlers
│
├── services/                    # Shared services
│   ├── __init__.py
│   ├── cache.py                # Redis caching
│   ├── queue.py                # Job queue
│   └── storage.py              # File storage
│
├── utils/                       # Utilities
│   ├── __init__.py
│   ├── logger.py               # Logging configuration
│   ├── validators.py           # Input validation
│   ├── image_utils.py          # Image processing
│   └── pdf_utils.py            # PDF processing
│
└── tests/                       # Test suite
    ├── __init__.py
    ├── conftest.py             # Pytest fixtures
    ├── unit/                   # Unit tests
    │   ├── __init__.py
    │   ├── test_ocr_engine.py
    │   ├── test_document_processor.py
    │   ├── test_output_parser.py
    │   ├── test_field_extractor.py
    │   ├── test_format_converter.py
    │   ├── test_model_manager.py
    │   ├── test_api_routes.py
    │   └── test_validators.py
    ├── integration/            # Integration tests
    │   ├── __init__.py
    │   ├── test_full_pipeline.py
    │   ├── test_api_endpoints.py
    │   └── test_gradio_ui.py
    └── fixtures/               # Test data
        ├── sample_invoice.pdf
        ├── sample_image.png
        └── expected_outputs/
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
POST /api/v1/ocr              - Process document
GET  /api/v1/ocr/{job_id}     - Get job status/result
GET  /api/v1/health           - Health check
GET  /api/v1/models           - List available models
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

### Sprint 1: Foundation (Week 1-2)

**Goal**: Basic project structure and core OCR working

- [ ] Set up project structure
- [ ] Implement `config.py` with all settings
- [ ] Port `core/ocr_engine.py` from notebook
- [ ] Port `core/document_processor.py`
- [ ] Port `models/model_manager.py`
- [ ] Port `models/hardware_detection.py`
- [ ] Basic unit tests for above
- [ ] Verify model loads and processes single image

**Milestone**: `python -m core.ocr_engine` processes test image

---

### Sprint 2: Processing Pipeline (Week 3-4)

**Goal**: Complete processing pipeline

- [ ] Implement `core/output_parser.py`
- [ ] Implement `core/field_extractor.py`
- [ ] Implement `core/format_converter.py`
- [ ] Implement `utils/` modules
- [ ] Unit tests for all core components
- [ ] Integration test for full pipeline

**Milestone**: End-to-end document processing works

---

### Sprint 3: API Layer (Week 5-6)

**Goal**: REST API with authentication

- [ ] Implement `api/server.py` (FastAPI)
- [ ] Implement `api/routes/ocr.py`
- [ ] Implement `api/routes/health.py`
- [ ] Implement `api/middleware/auth.py`
- [ ] Implement `api/schemas/`
- [ ] API unit tests
- [ ] API integration tests

**Milestone**: `curl` can process documents via API

---

### Sprint 4: Gradio UI (Week 7-8)

**Goal**: Full Gradio interface

- [ ] Implement `ui/app.py`
- [ ] Implement all UI components
- [ ] Connect UI to processing pipeline
- [ ] UI tests
- [ ] Documentation

**Milestone**: Gradio UI fully functional

---

### Sprint 5: Production Deployment (Week 9-10)

**Goal**: Docker deployment ready

- [ ] Create `Dockerfile`
- [ ] Create `docker-compose.yml`
- [ ] GitHub Actions CI/CD
- [ ] Environment documentation
- [ ] Performance benchmarks
- [ ] Security review

**Milestone**: `docker-compose up` runs full system

---

### Sprint 6: Enhanced Features (Week 11-12)

**Goal**: Production enhancements

- [ ] Redis caching
- [ ] Job queue (async processing)
- [ ] Webhook support
- [ ] Rate limiting
- [ ] Monitoring & logging
- [ ] Load testing

**Milestone**: Production-ready system

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

## License

[Add License]

---

## References

- Original notebooks: `nanonets-nanonets-ocr-s-imp-v6.ipynb`, `nanonets-nanonets-ocr2-3b-imp-v1.ipynb`
- Hugging Face Models: [Nanonets OCR Models](https://huggingface.co/nanonets)
- Development Workflow: `WORKFLOW.md`
