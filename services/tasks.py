"""
Celery tasks for background processing.
"""
import time
from typing import Dict, Any, Optional
from celery import shared_task
from celery.utils.log import get_task_logger

from utils.logger import ocr_logger, audit_logger

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    name="services.tasks.process_document",
    queue="gpu",
    max_retries=3,
    default_retry_delay=60
)
def process_document(
    self,
    document_id: str,
    file_path: str,
    config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Process a document through OCR.

    Args:
        document_id: Unique document identifier
        file_path: Path to the document file
        config: Processing configuration

    Returns:
        Processing results
    """
    config = config or {}

    try:
        ocr_logger.info(
            "Starting document processing",
            document_id=document_id,
            task_id=self.request.id
        )

        start_time = time.time()

        # Import here to avoid loading model on worker startup
        from core.ocr_engine import get_ocr_engine

        engine = get_ocr_engine()
        result = engine.process_document(
            file_path,
            max_tokens=config.get("max_tokens", 2048)
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Log completion
        ocr_logger.info(
            "Document processing completed",
            document_id=document_id,
            pages=result.metadata.total_pages,
            processing_time_ms=processing_time_ms
        )

        audit_logger.document_processed(
            document_id,
            result.metadata.total_pages,
            processing_time_ms
        )

        return {
            "status": "success",
            "document_id": document_id,
            "text": result.total_text,
            "pages": result.metadata.total_pages,
            "processing_time_ms": processing_time_ms,
            "metadata": {
                "filename": result.metadata.filename,
                "file_type": result.metadata.file_type,
                "file_size_mb": result.metadata.file_size_mb,
            }
        }

    except Exception as e:
        ocr_logger.error(
            "Document processing failed",
            document_id=document_id,
            error=str(e)
        )

        # Retry on failure
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="services.tasks.extract_fields",
    queue="default",
    max_retries=3
)
def extract_fields(
    self,
    document_id: str,
    text: str,
    fields: list = None,
    custom_fields: list = None
) -> Dict[str, Any]:
    """
    Extract fields from OCR text.
    """
    try:
        from core.field_extractor import FieldExtractor
        from config import PREDEFINED_FIELDS

        extractor = FieldExtractor()
        fields = fields or PREDEFINED_FIELDS
        custom_fields = custom_fields or []

        results = extractor.extract(text, fields, custom_fields)
        data = extractor.to_dict(results)

        return {
            "status": "success",
            "document_id": document_id,
            "fields": data,
            "statistics": extractor.get_statistics(results)
        }

    except Exception as e:
        logger.error(f"Field extraction failed: {e}")
        raise self.retry(exc=e)


@shared_task(
    name="services.tasks.send_webhook",
    queue="default",
    max_retries=5,
    default_retry_delay=30
)
def send_webhook(
    webhook_url: str,
    payload: Dict[str, Any],
    secret: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send webhook notification.
    """
    import requests
    import hmac
    import hashlib
    import json

    try:
        headers = {"Content-Type": "application/json"}

        # Add HMAC signature if secret provided
        if secret:
            body = json.dumps(payload)
            signature = hmac.new(
                secret.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        return {
            "status": "success",
            "status_code": response.status_code,
            "webhook_url": webhook_url
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Webhook delivery failed: {e}")
        raise


@shared_task(
    name="services.tasks.export_to_erp",
    queue="default",
    max_retries=3
)
def export_to_erp(
    document_id: str,
    connector_type: str,
    data: Dict[str, Any],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Export document data to ERP system.
    """
    try:
        from integrations.connectors import get_connector

        connector = get_connector(connector_type, config)
        result = connector.send(data)

        audit_logger.data_exported(document_id, "erp", connector_type)

        return {
            "status": "success",
            "document_id": document_id,
            "connector": connector_type,
            "result": result
        }

    except Exception as e:
        logger.error(f"ERP export failed: {e}")
        raise


@shared_task(name="services.tasks.cleanup_expired_jobs")
def cleanup_expired_jobs():
    """
    Clean up expired processing jobs.
    Runs periodically via Celery Beat.
    """
    from datetime import datetime, timedelta

    try:
        # Placeholder - would use database session
        logger.info("Running cleanup of expired jobs")

        return {"status": "success", "cleaned": 0}

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(name="services.tasks.update_usage_metrics")
def update_usage_metrics():
    """
    Update tenant usage metrics.
    Runs periodically via Celery Beat.
    """
    try:
        logger.info("Updating usage metrics")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Metrics update failed: {e}")
        return {"status": "error", "error": str(e)}
