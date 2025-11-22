"""
FastAPI application server.
"""
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

from config import settings
from api.routes import health, ocr, webhook
from api.middleware.auth import verify_api_key
from api.middleware.rate_limit import rate_limit_middleware

# Create FastAPI app
app = FastAPI(
    title="Nanonets VL OCR API",
    description="Enterprise-grade Vision-Language OCR API for document processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
if settings.api.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Add rate limiting middleware
@app.middleware("http")
async def add_rate_limiting(request: Request, call_next):
    return await rate_limit_middleware(request, call_next)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# Include routers
app.include_router(health.router, prefix=settings.api.api_prefix, tags=["Health"])
app.include_router(ocr.router, prefix=settings.api.api_prefix, tags=["OCR"])
app.include_router(webhook.router, prefix=settings.api.api_prefix, tags=["Webhooks"])


# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "Nanonets VL OCR API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": f"{settings.api.api_prefix}/health"
    }


def run_server():
    """Run the API server."""
    import uvicorn
    uvicorn.run(
        "api.server:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=False
    )


if __name__ == "__main__":
    print("=" * 60)
    print("API SERVER")
    print("=" * 60)
    print(f"  Starting server on {settings.api.host}:{settings.api.port}")
    print(f"  API prefix: {settings.api.api_prefix}")
    print(f"  Docs: http://{settings.api.host}:{settings.api.port}/docs")
    print("=" * 60)

    run_server()
