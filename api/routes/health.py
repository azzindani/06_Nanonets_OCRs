"""
Health, readiness, and metrics endpoints for production monitoring.
"""
import time
import torch
import psutil
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Response

from api.schemas.response import HealthResponse, ModelInfo
from models.model_manager import get_model_manager

router = APIRouter()

# Track startup time
START_TIME = time.time()

# Simple metrics store
metrics_store = {
    "requests_total": 0,
    "requests_success": 0,
    "requests_failed": 0,
    "documents_processed": 0,
    "pages_processed": 0,
    "processing_time_total_ms": 0,
}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.
    Returns 200 if the service is running.
    """
    model_manager = get_model_manager()
    model_info = model_manager.get_model_info()

    return HealthResponse(
        status="healthy",
        model_loaded=model_info.is_loaded,
        gpu_available=torch.cuda.is_available(),
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@router.get("/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes.
    Checks if all dependencies are available.
    """
    checks = {
        "api": True,
        "model": check_model_ready(),
        "storage": check_storage_ready(),
        "cache": check_cache_ready(),
    }

    all_ready = all(checks.values())

    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
        "uptime_seconds": int(time.time() - START_TIME)
    }


@router.get("/live")
async def liveness_check():
    """
    Liveness check for Kubernetes.
    Simple check that the service is responding.
    """
    return {"status": "alive"}


@router.get("/metrics")
async def get_metrics(response: Response):
    """
    Prometheus-compatible metrics endpoint.
    """
    # Get system metrics
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    gpu_memory = 0
    if torch.cuda.is_available():
        try:
            gpu_memory = torch.cuda.memory_allocated() / (1024**3)
        except:
            pass

    # Build Prometheus format
    metrics_text = f"""# HELP nanonets_uptime_seconds Time since service started
# TYPE nanonets_uptime_seconds gauge
nanonets_uptime_seconds {int(time.time() - START_TIME)}

# HELP nanonets_requests_total Total number of requests
# TYPE nanonets_requests_total counter
nanonets_requests_total {metrics_store['requests_total']}

# HELP nanonets_requests_success Successful requests
# TYPE nanonets_requests_success counter
nanonets_requests_success {metrics_store['requests_success']}

# HELP nanonets_requests_failed Failed requests
# TYPE nanonets_requests_failed counter
nanonets_requests_failed {metrics_store['requests_failed']}

# HELP nanonets_documents_processed Total documents processed
# TYPE nanonets_documents_processed counter
nanonets_documents_processed {metrics_store['documents_processed']}

# HELP nanonets_pages_processed Total pages processed
# TYPE nanonets_pages_processed counter
nanonets_pages_processed {metrics_store['pages_processed']}

# HELP nanonets_cpu_percent CPU usage percentage
# TYPE nanonets_cpu_percent gauge
nanonets_cpu_percent {cpu_percent}

# HELP nanonets_memory_percent Memory usage percentage
# TYPE nanonets_memory_percent gauge
nanonets_memory_percent {memory.percent}

# HELP nanonets_memory_used_bytes Memory used in bytes
# TYPE nanonets_memory_used_bytes gauge
nanonets_memory_used_bytes {memory.used}

# HELP nanonets_gpu_memory_gb GPU memory used in GB
# TYPE nanonets_gpu_memory_gb gauge
nanonets_gpu_memory_gb {gpu_memory:.2f}
"""

    return Response(content=metrics_text, media_type="text/plain")


@router.get("/metrics/json")
async def get_metrics_json():
    """
    JSON format metrics for dashboards.
    """
    memory = psutil.virtual_memory()

    return {
        "uptime_seconds": int(time.time() - START_TIME),
        "requests": {
            "total": metrics_store["requests_total"],
            "success": metrics_store["requests_success"],
            "failed": metrics_store["requests_failed"],
        },
        "documents": {
            "processed": metrics_store["documents_processed"],
            "pages": metrics_store["pages_processed"],
            "avg_processing_time_ms": (
                metrics_store["processing_time_total_ms"] / max(metrics_store["documents_processed"], 1)
            ),
        },
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": memory.percent,
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "gpu_available": torch.cuda.is_available(),
        }
    }


@router.get("/models", response_model=ModelInfo)
async def get_model_info():
    """
    Get information about the loaded model.
    """
    model_manager = get_model_manager()
    info = model_manager.get_model_info()

    return ModelInfo(
        name=info.name,
        device=info.device,
        quantization=info.quantization,
        memory_used_gb=info.memory_used_gb,
        is_loaded=info.is_loaded
    )


def check_model_ready() -> bool:
    """Check if OCR model is loaded and ready."""
    try:
        manager = get_model_manager()
        return manager._model is not None
    except:
        return False


def check_storage_ready() -> bool:
    """Check if storage service is available."""
    try:
        from services.storage import StorageService
        storage = StorageService()
        return storage.health_check()
    except:
        return True  # Default to True if not configured


def check_cache_ready() -> bool:
    """Check if cache service is available."""
    try:
        from services.cache import CacheService
        cache = CacheService()
        return cache.health_check()
    except:
        return True  # Default to True if not configured


def increment_metric(name: str, value: int = 1):
    """Increment a metric counter."""
    if name in metrics_store:
        metrics_store[name] += value


def record_document_processed(pages: int, processing_time_ms: int):
    """Record document processing metrics."""
    metrics_store["documents_processed"] += 1
    metrics_store["pages_processed"] += pages
    metrics_store["processing_time_total_ms"] += processing_time_ms
