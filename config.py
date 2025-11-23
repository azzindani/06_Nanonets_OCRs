"""
Central configuration for Nanonets VL OCR system.
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ModelConfig:
    """Model configuration settings."""
    name: str = "nanonets/Nanonets-OCR2-3B"
    quantization: str = "8bit"
    torch_dtype: str = "float16"
    device_map: str = "auto"
    low_cpu_mem_usage: bool = True
    attn_implementation: str = "eager"


@dataclass
class ProcessingConfig:
    """Processing configuration settings."""
    max_image_size: int = 1536
    max_tokens: int = 4096  # Increased for OCR2-3B model
    default_dpi: int = 150
    supported_image_formats: List[str] = field(default_factory=lambda: [
        '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'
    ])
    supported_document_formats: List[str] = field(default_factory=lambda: ['.pdf'])


@dataclass
class APIConfig:
    """API server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    api_key: str = ""
    rate_limit: int = 100
    enable_cors: bool = True
    api_prefix: str = "/api/v1"


@dataclass
class UIConfig:
    """Gradio UI configuration."""
    server_name: str = "0.0.0.0"
    server_port: int = 7860
    share: bool = False
    theme: str = "default"


@dataclass
class CacheConfig:
    """Caching configuration."""
    redis_url: str = "redis://localhost:6379"
    cache_ttl: int = 3600
    enable_cache: bool = False


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"
    file_path: Optional[str] = None


@dataclass
class Settings:
    """Main application settings."""
    model: ModelConfig = field(default_factory=ModelConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    api: APIConfig = field(default_factory=APIConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    storage_path: str = "/data/documents"

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        settings = cls()

        # Model settings
        settings.model.name = os.getenv("MODEL_NAME", settings.model.name)
        settings.model.quantization = os.getenv("MODEL_QUANTIZATION", settings.model.quantization)

        # Processing settings
        settings.processing.max_image_size = int(os.getenv("MAX_IMAGE_SIZE", settings.processing.max_image_size))
        settings.processing.max_tokens = int(os.getenv("MAX_TOKENS", settings.processing.max_tokens))

        # API settings
        settings.api.host = os.getenv("API_HOST", settings.api.host)
        settings.api.port = int(os.getenv("API_PORT", settings.api.port))
        settings.api.api_key = os.getenv("API_KEY", settings.api.api_key)
        settings.api.rate_limit = int(os.getenv("RATE_LIMIT", settings.api.rate_limit))

        # UI settings
        settings.ui.server_name = os.getenv("GRADIO_SERVER_NAME", settings.ui.server_name)
        settings.ui.server_port = int(os.getenv("GRADIO_SERVER_PORT", settings.ui.server_port))
        settings.ui.share = os.getenv("GRADIO_SHARE", "false").lower() == "true"

        # Cache settings
        settings.cache.redis_url = os.getenv("REDIS_URL", settings.cache.redis_url)
        settings.cache.enable_cache = os.getenv("ENABLE_CACHE", "false").lower() == "true"

        # Logging settings
        settings.logging.level = os.getenv("LOG_LEVEL", settings.logging.level)
        settings.logging.format = os.getenv("LOG_FORMAT", settings.logging.format)

        # Storage
        settings.storage_path = os.getenv("STORAGE_PATH", settings.storage_path)

        return settings


# Predefined fields for document extraction
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

# Default OCR prompt
DEFAULT_OCR_PROMPT = """Extract the text from the above document as if you were reading it naturally. Return the tables in html format. Return the equations in LaTeX representation. If there is an image in the document and image caption is not present, add a small description of the image inside the <img></img> tag; otherwise, add the image caption inside <img></img>. Watermarks should be wrapped in brackets. Ex: <watermark>OFFICIAL COPY</watermark>. Page numbers should be wrapped in brackets. Ex: <page_number>14</page_number> or <page_number>9/22</page_number>. Prefer using ☐ and ☑ for check boxes."""

# Global settings instance
settings = Settings.from_env()


if __name__ == "__main__":
    print("=" * 60)
    print("CONFIG MODULE TEST")
    print("=" * 60)

    # Test settings loading
    test_settings = Settings.from_env()
    print(f"  Model name: {test_settings.model.name}")
    print(f"  Max tokens: {test_settings.processing.max_tokens}")
    print(f"  API port: {test_settings.api.port}")
    print(f"  Predefined fields: {len(PREDEFINED_FIELDS)}")
    print(f"  ✓ Settings loaded successfully")

    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
