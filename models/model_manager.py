"""
Model manager for loading, caching, and managing VL models.
"""
import torch
from typing import Optional, Tuple, Any
from dataclasses import dataclass

from transformers import AutoTokenizer, AutoProcessor, AutoModelForImageTextToText

from models.hardware_detection import detect_hardware, clear_memory, set_memory_optimizations, HardwareConfig


@dataclass
class ModelInfo:
    """Information about the loaded model."""
    name: str
    device: str
    quantization: str
    memory_used_gb: float
    is_loaded: bool


class ModelManager:
    """
    Manages loading and caching of VL models.

    Supports lazy loading and memory optimization.
    """

    def __init__(self, model_name: str = "nanonets/Nanonets-OCR-s"):
        """
        Initialize the model manager.

        Args:
            model_name: HuggingFace model path.
        """
        self.model_name = model_name
        self._model: Optional[Any] = None
        self._tokenizer: Optional[Any] = None
        self._processor: Optional[Any] = None
        self._hardware_config: Optional[HardwareConfig] = None
        self._is_loaded = False

    def load_model(self) -> Tuple[Any, Any, Any]:
        """
        Load the model with optimal settings for detected hardware.

        Returns:
            Tuple of (model, tokenizer, processor)
        """
        if self._is_loaded:
            return self._model, self._tokenizer, self._processor

        # Set memory optimizations
        set_memory_optimizations()

        # Detect hardware
        self._hardware_config = detect_hardware()
        device = self._hardware_config.device

        print(f"[{device}] Loading model: {self.model_name}")

        try:
            if device == "cuda":
                print(f"[{device}] CUDA available. Loading with optimizations.")

                # Determine load parameters based on quantization
                load_kwargs = {
                    "device_map": "auto",
                    "low_cpu_mem_usage": True,
                    "torch_dtype": "auto",  # Let model decide optimal dtype
                }

                # Add quantization if specified
                if self._hardware_config.quantization == "8bit":
                    load_kwargs["load_in_8bit"] = True
                elif self._hardware_config.quantization == "4bit":
                    load_kwargs["load_in_4bit"] = True

                # Try flash_attention_2 first, then eager
                try:
                    load_kwargs["attn_implementation"] = "flash_attention_2"
                    self._model = AutoModelForImageTextToText.from_pretrained(
                        self.model_name,
                        **load_kwargs
                    )
                    print("Using flash_attention_2")
                except Exception as attn_error:
                    # Fallback to eager attention if flash_attention_2 fails
                    print(f"Flash attention not available, using eager: {attn_error}")
                    load_kwargs["attn_implementation"] = "eager"
                    self._model = AutoModelForImageTextToText.from_pretrained(
                        self.model_name,
                        **load_kwargs
                    )

                torch.cuda.empty_cache()
                memory_used = torch.cuda.memory_allocated(0) / (1024 ** 3)
                print(f"Model loaded. VRAM used: {memory_used:.2f} GB")

            else:
                print(f"[{device}] CUDA not available. Loading on CPU.")
                self._model = AutoModelForImageTextToText.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32,
                    device_map="cpu",
                )

        except Exception as e:
            print(f"[{device}] Warning: Optimized loading failed: {e}")
            # Fallback loading
            try:
                self._model = AutoModelForImageTextToText.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                    device_map="auto" if device == "cuda" else "cpu",
                    low_cpu_mem_usage=True
                )
            except Exception as e2:
                print(f"[{device}] Falling back to CPU. Error: {e2}")
                self._model = AutoModelForImageTextToText.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32,
                    device_map="cpu",
                )

        # Set model to evaluation mode
        self._model.eval()

        # Load tokenizer and processor
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._processor = AutoProcessor.from_pretrained(self.model_name)

        self._is_loaded = True

        return self._model, self._tokenizer, self._processor

    def unload_model(self):
        """Unload the model and free memory."""
        if self._model is not None:
            del self._model
            self._model = None

        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None

        if self._processor is not None:
            del self._processor
            self._processor = None

        self._is_loaded = False
        clear_memory()
        print("Model unloaded and memory cleared.")

    def get_model_info(self) -> ModelInfo:
        """Get information about the loaded model."""
        memory_used = 0.0
        if torch.cuda.is_available() and self._is_loaded:
            memory_used = torch.cuda.memory_allocated(0) / (1024 ** 3)

        device = "cpu"
        quantization = "none"

        if self._hardware_config:
            device = self._hardware_config.device
            quantization = self._hardware_config.quantization

        return ModelInfo(
            name=self.model_name,
            device=device,
            quantization=quantization,
            memory_used_gb=memory_used,
            is_loaded=self._is_loaded
        )

    def get_model(self) -> Any:
        """Get the loaded model, loading if necessary."""
        if not self._is_loaded:
            self.load_model()
        return self._model

    def get_processor(self) -> Any:
        """Get the loaded processor, loading if necessary."""
        if not self._is_loaded:
            self.load_model()
        return self._processor

    def get_tokenizer(self) -> Any:
        """Get the loaded tokenizer, loading if necessary."""
        if not self._is_loaded:
            self.load_model()
        return self._tokenizer

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._is_loaded

    @property
    def device(self) -> str:
        """Get the device the model is loaded on."""
        if self._model is not None:
            return str(self._model.device)
        return "not loaded"


# Global model manager instance
_model_manager: Optional[ModelManager] = None


def get_model_manager(model_name: str = "nanonets/Nanonets-OCR-s") -> ModelManager:
    """
    Get or create the global model manager instance.

    Args:
        model_name: HuggingFace model path.

    Returns:
        ModelManager instance.
    """
    global _model_manager
    if _model_manager is None or _model_manager.model_name != model_name:
        _model_manager = ModelManager(model_name)
    return _model_manager


if __name__ == "__main__":
    print("=" * 60)
    print("MODEL MANAGER MODULE TEST")
    print("=" * 60)

    # Test model manager creation
    manager = ModelManager("nanonets/Nanonets-OCR-s")
    info = manager.get_model_info()

    print(f"  Model name: {info.name}")
    print(f"  Is loaded: {info.is_loaded}")
    print(f"  ✓ Model manager created successfully")

    # Note: Actual model loading requires GPU and downloads
    # Uncomment below to test full loading
    # manager.load_model()
    # info = manager.get_model_info()
    # print(f"  Device: {info.device}")
    # print(f"  Memory used: {info.memory_used_gb:.2f} GB")

    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
