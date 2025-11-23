"""
Main OCR engine for document text extraction.
"""
import time
from datetime import timedelta
from dataclasses import dataclass
from typing import List, Optional, Any

import torch
from PIL import Image

from config import settings, DEFAULT_OCR_PROMPT
from models.model_manager import get_model_manager
from models.hardware_detection import clear_memory
from core.document_processor import DocumentProcessor, FileMetadata


@dataclass
class OCRResult:
    """Result from OCR processing."""
    text: str
    page_number: int
    processing_time_seconds: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class DocumentOCRResult:
    """Complete result from processing a document."""
    pages: List[OCRResult]
    total_text: str
    total_processing_time: str
    metadata: FileMetadata
    processed_images: List[Image.Image]


class OCREngine:
    """
    Main OCR engine for processing documents with VL models.
    """

    def __init__(self, model_name: str = None, max_tokens: int = None):
        """
        Initialize the OCR engine.

        Args:
            model_name: HuggingFace model path.
            max_tokens: Maximum tokens for generation.
        """
        self.model_name = model_name or settings.model.name
        self.max_tokens = max_tokens or settings.processing.max_tokens
        self._model_manager = get_model_manager(self.model_name)
        self._document_processor = DocumentProcessor()

    def initialize(self):
        """
        Pre-load the model and processor.
        Call this before processing to avoid cold start on first request.
        """
        print(f"Loading model: {self.model_name}")
        self._model_manager.get_model()
        self._model_manager.get_processor()
        print("Model and processor loaded successfully")

    def _process_single_image(self, image: Image.Image, prompt: str, max_tokens: int) -> str:
        """
        Process a single image through the model.

        Args:
            image: PIL Image to process.
            prompt: OCR prompt.
            max_tokens: Maximum tokens for generation.

        Returns:
            Extracted text from the image.
        """
        model = self._model_manager.get_model()
        processor = self._model_manager.get_processor()

        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt},
                ]},
            ]

            text_for_processor = processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = processor(
                text=[text_for_processor],
                images=[image],
                padding=True,
                return_tensors="pt"
            )

            # Get the device - handle device_map="auto" case
            if hasattr(model, 'device'):
                device = model.device
            else:
                # For models with device_map="auto", use cuda:0
                device = "cuda:0" if torch.cuda.is_available() else "cpu"

            inputs = {k: v.to(device) for k, v in inputs.items()}

            with torch.no_grad():
                output_ids = model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    do_sample=False,
                    use_cache=True
                )

            # Slice output to get only generated tokens
            input_ids_length = inputs['input_ids'].shape[1]
            generated_ids = [output_ids[0, input_ids_length:]]
            output_text = processor.batch_decode(
                generated_ids,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )[0]

            del inputs, output_ids, generated_ids
            clear_memory()

            return output_text

        except torch.cuda.OutOfMemoryError as e:
            clear_memory()
            return f"CUDA out of memory error. Try reducing max_tokens or image resolution. Error: {e}"
        except Exception as e:
            clear_memory()
            return f"Error processing image: {e}"

    def process_image(self, image: Image.Image, prompt: str = None, max_tokens: int = None) -> OCRResult:
        """
        Process a single image and return OCR result.

        Args:
            image: PIL Image to process.
            prompt: OCR prompt (uses default if not provided).
            max_tokens: Maximum tokens for generation.

        Returns:
            OCRResult with extracted text.
        """
        prompt = prompt or DEFAULT_OCR_PROMPT
        max_tokens = max_tokens or self.max_tokens

        start_time = time.time()
        text = self._process_single_image(image, prompt, max_tokens)
        elapsed = time.time() - start_time

        success = not text.startswith("Error") and not text.startswith("CUDA")

        return OCRResult(
            text=text,
            page_number=1,
            processing_time_seconds=elapsed,
            success=success,
            error_message=None if success else text
        )

    def process_document(self, file_path: str, prompt: str = None, max_tokens: int = None) -> DocumentOCRResult:
        """
        Process a complete document (image or PDF).

        Args:
            file_path: Path to the document file.
            prompt: OCR prompt (uses default if not provided).
            max_tokens: Maximum tokens for generation.

        Returns:
            DocumentOCRResult with all pages processed.
        """
        prompt = prompt or DEFAULT_OCR_PROMPT
        max_tokens = max_tokens or self.max_tokens

        start_time = time.time()

        # Load and process the document
        images, metadata = self._document_processor.process_file(file_path)

        results = []
        processed_images = []

        for i, image in enumerate(images):
            page_start = time.time()
            print(f"Processing page {i + 1}/{len(images)}...")

            text = self._process_single_image(image, prompt, max_tokens)
            page_elapsed = time.time() - page_start

            success = not text.startswith("Error") and not text.startswith("CUDA")

            results.append(OCRResult(
                text=text,
                page_number=i + 1,
                processing_time_seconds=page_elapsed,
                success=success,
                error_message=None if success else text
            ))

            processed_images.append(image.copy())

            print(f"Page {i + 1} completed in {page_elapsed:.2f}s")

        # Combine all text
        all_text = []
        for result in results:
            all_text.append(f"\n--- Page {result.page_number} ---\n{result.text}")

        total_time = time.time() - start_time
        elapsed_str = str(timedelta(seconds=int(total_time)))

        # Update metadata with processing time
        metadata = FileMetadata(
            filename=metadata.filename,
            file_size_mb=metadata.file_size_mb,
            file_type=metadata.file_type,
            total_pages=metadata.total_pages,
            dimensions=metadata.dimensions
        )

        return DocumentOCRResult(
            pages=results,
            total_text="\n\n".join(all_text),
            total_processing_time=elapsed_str,
            metadata=metadata,
            processed_images=processed_images
        )

    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        info = self._model_manager.get_model_info()
        return {
            "name": info.name,
            "device": info.device,
            "quantization": info.quantization,
            "memory_used_gb": info.memory_used_gb,
            "is_loaded": info.is_loaded
        }


# Global OCR engine instance
_ocr_engine: Optional[OCREngine] = None


def get_ocr_engine(model_name: str = None) -> OCREngine:
    """
    Get or create the global OCR engine instance.

    Args:
        model_name: HuggingFace model path.

    Returns:
        OCREngine instance.
    """
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = OCREngine(model_name)
    return _ocr_engine


if __name__ == "__main__":
    print("=" * 60)
    print("OCR ENGINE MODULE TEST")
    print("=" * 60)

    # Test engine creation
    engine = OCREngine()
    print(f"  Model name: {engine.model_name}")
    print(f"  Max tokens: {engine.max_tokens}")
    print(f"  ✓ OCR engine created successfully")

    # Note: Actual processing requires model loading
    # Uncomment below to test with a real file
    # result = engine.process_document("test.pdf")
    # print(f"  Pages processed: {len(result.pages)}")
    # print(f"  Total time: {result.total_processing_time}")

    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
