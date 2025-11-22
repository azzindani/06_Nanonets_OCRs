"""
Structured JSON logging for production with context tracking and audit trail.
"""
import logging
import json
import sys
import uuid
import time
from datetime import datetime
from typing import Optional, Any, Dict
from contextvars import ContextVar
from functools import wraps

from config import settings

# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
user_id_var: ContextVar[str] = ContextVar('user_id', default='')
tenant_id_var: ContextVar[str] = ContextVar('tenant_id', default='')


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add context variables
        if request_id_var.get():
            log_data["request_id"] = request_id_var.get()
        if user_id_var.get():
            log_data["user_id"] = user_id_var.get()
        if tenant_id_var.get():
            log_data["tenant_id"] = tenant_id_var.get()

        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)

        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class StructuredLogger:
    """Logger with structured JSON output and context tracking."""

    def __init__(self, name: str, level: int = None):
        self.logger = logging.getLogger(name)
        log_level = level or getattr(logging, settings.logging.level.upper())
        self.logger.setLevel(log_level)

        # Remove existing handlers
        self.logger.handlers = []

        # Add JSON handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

        # Add file handler if configured
        if settings.logging.file_path:
            file_handler = logging.FileHandler(settings.logging.file_path)
            file_handler.setFormatter(JSONFormatter())
            self.logger.addHandler(file_handler)

    def _log(self, level: int, message: str, **kwargs):
        """Log with extra data."""
        record = self.logger.makeRecord(
            self.logger.name, level, "", 0, message, (), None
        )
        if kwargs:
            record.extra_data = kwargs
        self.logger.handle(record)

    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs):
        self.logger.exception(message, extra={'extra_data': kwargs})


# Global loggers for different components
app_logger = StructuredLogger("nanonets.app")
ocr_logger = StructuredLogger("nanonets.ocr")
api_logger = StructuredLogger("nanonets.api")
auth_logger = StructuredLogger("nanonets.auth")
db_logger = StructuredLogger("nanonets.db")

# Backwards compatibility
logger = app_logger.logger


def setup_logger(name: str = "nanonets-vl", level: str = None) -> logging.Logger:
    """Legacy function for backwards compatibility."""
    structured = StructuredLogger(name, getattr(logging, (level or "INFO").upper()))
    return structured.logger


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return f"req_{uuid.uuid4().hex[:16]}"


def set_request_context(request_id: str = None, user_id: str = None, tenant_id: str = None):
    """Set context variables for the current request."""
    if request_id:
        request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if tenant_id:
        tenant_id_var.set(tenant_id)


def clear_request_context():
    """Clear context variables."""
    request_id_var.set('')
    user_id_var.set('')
    tenant_id_var.set('')


def log_execution_time(logger: StructuredLogger = None):
    """Decorator to log function execution time."""
    if logger is None:
        logger = app_logger

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = int((time.time() - start) * 1000)
                logger.info(
                    f"{func.__name__} completed",
                    function=func.__name__,
                    duration_ms=elapsed_ms,
                    status="success"
                )
                return result
            except Exception as e:
                elapsed_ms = int((time.time() - start) * 1000)
                logger.error(
                    f"{func.__name__} failed",
                    function=func.__name__,
                    duration_ms=elapsed_ms,
                    status="error",
                    error=str(e)
                )
                raise
        return wrapper
    return decorator


class AuditLogger:
    """Logger for audit trail events."""

    def __init__(self):
        self.logger = StructuredLogger("nanonets.audit", logging.INFO)

    def log_event(self, action: str, resource_type: str, resource_id: str,
                  details: Dict[str, Any] = None, outcome: str = "success"):
        """Log an audit event."""
        self.logger.info(
            f"Audit: {action}",
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            details=details or {}
        )

    def document_uploaded(self, document_id: str, filename: str, file_size: int):
        self.log_event(
            "document_uploaded",
            "document",
            document_id,
            {"filename": filename, "file_size_bytes": file_size}
        )

    def document_processed(self, document_id: str, pages: int, processing_time_ms: int):
        self.log_event(
            "document_processed",
            "document",
            document_id,
            {"pages": pages, "processing_time_ms": processing_time_ms}
        )

    def user_login(self, user_id: str, method: str):
        self.log_event("user_login", "user", user_id, {"method": method})

    def user_logout(self, user_id: str):
        self.log_event("user_logout", "user", user_id)

    def api_key_created(self, key_id: str, user_id: str):
        self.log_event("api_key_created", "api_key", key_id, {"user_id": user_id})

    def data_exported(self, document_id: str, format: str, destination: str):
        self.log_event(
            "data_exported",
            "document",
            document_id,
            {"format": format, "destination": destination}
        )


audit_logger = AuditLogger()


if __name__ == "__main__":
    print("=" * 60)
    print("LOGGER MODULE TEST")
    print("=" * 60)

    # Test structured logger
    set_request_context(
        request_id=generate_request_id(),
        user_id="user_123",
        tenant_id="tenant_456"
    )

    app_logger.info("Test message", action="test", value=42)
    ocr_logger.info("OCR processing", pages=5, confidence=0.95)
    api_logger.warning("Rate limit approaching", remaining=10)

    # Test audit logger
    audit_logger.document_uploaded("doc_abc", "invoice.pdf", 102400)
    audit_logger.document_processed("doc_abc", 3, 1250)

    clear_request_context()

    print("\n  ✓ Logger tests passed")
    print("=" * 60)
