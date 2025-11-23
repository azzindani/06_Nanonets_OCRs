"""
OCR processing endpoints.
"""
import os
import time
import uuid
import tempfile
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query

from api.schemas.response import OCRResponse, DocumentMetadata, ErrorResponse
from core.ocr_engine import get_ocr_engine
from core.output_parser import OutputParser
from core.field_extractor import FieldExtractor
from core.format_converter import FormatConverter
from core.structured_output import get_structured_processor
from core.document_classifier import get_document_classifier
from core.language_support import get_language_detector
from config import PREDEFINED_FIELDS

router = APIRouter()


@router.post("/ocr", response_model=OCRResponse)
async def process_document(
    file: UploadFile = File(...),
    max_tokens: int = Form(default=2048),
    max_image_size: int = Form(default=1536),
    output_format: str = Form(default="json"),
    extract_fields: bool = Form(default=True),
    structured_output: bool = Form(default=True),
    detect_language: bool = Form(default=True),
    classify_document: bool = Form(default=True),
    webhook_url: Optional[str] = Form(default=None),
    confidence_threshold: float = Form(default=0.75)
):
    """
    Process a document with OCR.

    Args:
        file: Document file (PDF or image).
        max_tokens: Maximum tokens for generation.
        max_image_size: Maximum image dimension.
        output_format: Output format (json, xml, csv).
        extract_fields: Whether to extract predefined fields.
        structured_output: Whether to return enhanced structured output.
        detect_language: Whether to detect document language.
        classify_document: Whether to classify document type.
        webhook_url: URL for webhook callback.
        confidence_threshold: Minimum confidence for field extraction.

    Returns:
        OCRResponse with extracted data.
    """
    job_id = str(uuid.uuid4())
    start_time = time.time()

    # Validate file type
    filename = file.filename or "document"
    extension = os.path.splitext(filename)[1].lower()

    supported = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.pdf']
    if extension not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {extension}"
        )

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Get OCR engine
        engine = get_ocr_engine()

        # Process document
        result = engine.process_document(
            tmp_path,
            max_tokens=max_tokens
        )

        # Parse output
        parser = OutputParser()
        parsed = parser.parse(result.total_text)

        # Get tables HTML for structured processing
        tables_html = []
        for page in parsed.pages:
            tables_html.extend(page.tables_html)

        # Document classification
        document_type = None
        classification_confidence = None
        if classify_document:
            classifier = get_document_classifier()
            classification = classifier.classify(result.total_text)
            document_type = classification.document_type.value
            classification_confidence = round(classification.confidence, 2)

        # Language detection
        detected_language = None
        if detect_language:
            detector = get_language_detector()
            lang_result = detector.detect(result.total_text)
            detected_language = lang_result.primary_language.value

        # Enhanced structured output
        structured_result = None
        if structured_output:
            processor = get_structured_processor()
            structured_result = processor.process(result.total_text, tables_html)

        # Convert to requested format
        converter = FormatConverter()

        if output_format == "json":
            formatted_output = converter.to_json(parsed)
        elif output_format == "xml":
            formatted_output = converter.to_xml(parsed)
        else:
            formatted_output = converter.to_json(parsed)

        # Extract fields if requested
        extracted_fields = None
        confidence_scores = None

        if extract_fields:
            extractor = FieldExtractor()
            field_results = extractor.extract(
                result.total_text,
                enabled_fields=PREDEFINED_FIELDS
            )
            extracted_fields = extractor.to_dict(field_results)
            confidence_scores = extractor.get_confidence_scores(field_results)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Build result object
        result_data = {
            "text": result.total_text,
            "pages": [
                {
                    "page_number": page.page_number,
                    "text": page.text,
                    "success": page.success
                }
                for page in result.pages
            ],
            "tables_count": sum(len(p.tables_html) for p in parsed.pages),
            "equations_count": sum(len(p.latex_equations) for p in parsed.pages),
            "formatted_output": formatted_output
        }

        # Add enhanced features to result
        if document_type:
            result_data["document_type"] = document_type
            result_data["classification_confidence"] = classification_confidence

        if detected_language:
            result_data["language"] = detected_language

        if structured_result:
            result_data["structured"] = structured_result

        # Build response
        response = OCRResponse(
            job_id=job_id,
            status="completed",
            processing_time_ms=processing_time_ms,
            document=DocumentMetadata(
                filename=filename,
                file_size_mb=len(content) / (1024 * 1024),
                file_type=extension.upper().replace('.', ''),
                total_pages=result.metadata.total_pages
            ),
            result=result_data,
            extracted_fields=extracted_fields,
            confidence_scores=confidence_scores
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/ocr/{job_id}")
async def get_job_status(job_id: str):
    """
    Get status of an OCR job.

    For synchronous processing, this always returns completed.
    For async processing (future), this would check job queue.
    """
    return {
        "job_id": job_id,
        "status": "completed",
        "message": "Synchronous processing - job completed immediately"
    }


@router.post("/classify")
async def classify_document(
    file: UploadFile = File(None),
    text: str = Form(None)
):
    """
    Classify document type from file or text.

    Args:
        file: Optional document file
        text: Optional text content

    Returns:
        Classification result with document type and confidence.
    """
    if not file and not text:
        raise HTTPException(
            status_code=400,
            detail="Either file or text must be provided"
        )

    # Get text from file if provided
    if file:
        # Save and process file
        filename = file.filename or "document"
        extension = os.path.splitext(filename)[1].lower()

        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            engine = get_ocr_engine()
            result = engine.process_document(tmp_path)
            text = result.total_text
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # Classify
    classifier = get_document_classifier()
    result = classifier.classify(text)

    return {
        "document_type": result.document_type.value,
        "confidence": round(result.confidence, 2),
        "all_scores": {k: round(v, 3) for k, v in result.all_scores.items()},
        "keywords_found": result.keywords_found
    }


@router.post("/detect-language")
async def detect_language(
    file: UploadFile = File(None),
    text: str = Form(None)
):
    """
    Detect language of document.

    Args:
        file: Optional document file
        text: Optional text content

    Returns:
        Language detection result.
    """
    if not file and not text:
        raise HTTPException(
            status_code=400,
            detail="Either file or text must be provided"
        )

    # Get text from file if provided
    if file:
        filename = file.filename or "document"
        extension = os.path.splitext(filename)[1].lower()

        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            engine = get_ocr_engine()
            result = engine.process_document(tmp_path)
            text = result.total_text
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # Detect language
    detector = get_language_detector()
    result = detector.detect(text)

    return {
        "primary_language": result.primary_language.value,
        "confidence": round(result.confidence, 2),
        "script_detected": result.script_detected,
        "is_multilingual": result.is_multilingual,
        "secondary_languages": [lang.value for lang in result.secondary_languages]
    }


@router.post("/extract-entities")
async def extract_entities(
    file: UploadFile = File(None),
    text: str = Form(None)
):
    """
    Extract entities from document.

    Args:
        file: Optional document file
        text: Optional text content

    Returns:
        Extracted entities and semantic fields.
    """
    from core.semantic_extractor import get_semantic_extractor

    if not file and not text:
        raise HTTPException(
            status_code=400,
            detail="Either file or text must be provided"
        )

    # Get text from file if provided
    if file:
        filename = file.filename or "document"
        extension = os.path.splitext(filename)[1].lower()

        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            engine = get_ocr_engine()
            result = engine.process_document(tmp_path)
            text = result.total_text
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # Extract entities
    extractor = get_semantic_extractor()
    result = extractor.extract(text)

    return {
        "entities": result.entities,
        "fields": {
            name: {
                "value": field.value,
                "confidence": field.confidence,
                "context": field.context
            }
            for name, field in result.fields.items()
        },
        "summary": result.summary,
        "key_points": result.key_points
    }


@router.post("/v2/ocr")
async def process_document_v2(
    file: UploadFile = File(...),
    max_tokens: int = Form(default=2048),
    webhook_url: Optional[str] = Form(default=None)
):
    """
    API v2 - Process document with enhanced structured output.

    Returns clean, structured format optimized for downstream processing.
    Includes document classification, field extraction, entities, and line items.

    Args:
        file: Document file (PDF or image)
        max_tokens: Maximum tokens for generation
        webhook_url: Optional webhook URL for callback

    Returns:
        Structured output with extracted fields as key-value pairs.
    """
    job_id = str(uuid.uuid4())
    start_time = time.time()

    filename = file.filename or "document"
    extension = os.path.splitext(filename)[1].lower()

    supported = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.pdf']
    if extension not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {extension}"
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Process with OCR
        engine = get_ocr_engine()
        result = engine.process_document(tmp_path, max_tokens=max_tokens)

        # Parse to get tables
        parser = OutputParser()
        parsed = parser.parse(result.total_text)

        tables_html = []
        for page in parsed.pages:
            tables_html.extend(page.tables_html)

        # Get structured output
        processor = get_structured_processor()
        structured = processor.process(result.total_text, tables_html)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Build v2 response
        response = {
            "api_version": "2.0",
            "job_id": job_id,
            "status": "completed",
            "processing_time_ms": processing_time_ms,
            "document": {
                "filename": filename,
                "file_size_mb": round(len(content) / (1024 * 1024), 3),
                "file_type": extension.upper().replace('.', ''),
                "total_pages": result.metadata.total_pages
            },
            "result": structured
        }

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/structured")
async def get_structured_output(
    file: UploadFile = File(...),
    max_tokens: int = Form(default=2048)
):
    """
    Get fully structured output from document.

    Args:
        file: Document file (PDF or image)
        max_tokens: Maximum tokens for generation

    Returns:
        Enhanced structured output with all extracted data.
    """
    filename = file.filename or "document"
    extension = os.path.splitext(filename)[1].lower()

    supported = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.pdf']
    if extension not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {extension}"
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Process with OCR
        engine = get_ocr_engine()
        result = engine.process_document(tmp_path, max_tokens=max_tokens)

        # Parse to get tables
        parser = OutputParser()
        parsed = parser.parse(result.total_text)

        tables_html = []
        for page in parsed.pages:
            tables_html.extend(page.tables_html)

        # Get structured output
        processor = get_structured_processor()
        structured = processor.process(result.total_text, tables_html)

        return structured

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
