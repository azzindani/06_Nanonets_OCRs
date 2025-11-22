"""Tests for language support functionality."""
import pytest
from core.language_support import (
    LanguageDetector,
    MultiLanguageProcessor,
    Language,
    LanguageDetectionResult,
    get_language_detector,
    get_multi_language_processor
)


class TestLanguageDetector:
    """Test language detection functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = LanguageDetector()

    def test_detect_english(self):
        """Test detection of English text."""
        text = "The quick brown fox jumps over the lazy dog. This is a sample English text."
        result = self.detector.detect(text)

        assert isinstance(result, LanguageDetectionResult)
        assert result.primary_language == Language.ENGLISH
        assert result.confidence > 0.3
        assert result.script_detected == "latin"

    def test_detect_spanish(self):
        """Test detection of Spanish text."""
        text = "El rápido zorro marrón salta sobre el perro perezoso. ¿Qué tal?"
        result = self.detector.detect(text)

        assert result.primary_language == Language.SPANISH
        assert result.script_detected == "latin"

    def test_detect_french(self):
        """Test detection of French text."""
        text = "Le renard brun rapide saute par-dessus le chien paresseux. C'est un texte en français."
        result = self.detector.detect(text)

        assert result.primary_language == Language.FRENCH

    def test_detect_german(self):
        """Test detection of German text."""
        text = "Der schnelle braune Fuchs springt über den faulen Hund. Das ist ein deutscher Text."
        result = self.detector.detect(text)

        assert result.primary_language == Language.GERMAN

    def test_detect_russian(self):
        """Test detection of Russian text."""
        text = "Это текст на русском языке. Привет, как дела?"
        result = self.detector.detect(text)

        assert result.primary_language == Language.RUSSIAN
        assert result.script_detected == "cyrillic"

    def test_detect_chinese(self):
        """Test detection of Chinese text."""
        text = "这是一段中文文本。你好，世界！"
        result = self.detector.detect(text)

        assert result.primary_language == Language.CHINESE
        assert result.script_detected == "cjk"

    def test_detect_japanese(self):
        """Test detection of Japanese text."""
        text = "これは日本語のテキストです。こんにちは。"
        result = self.detector.detect(text)

        assert result.primary_language == Language.JAPANESE
        assert result.script_detected == "japanese"

    def test_detect_korean(self):
        """Test detection of Korean text."""
        text = "이것은 한국어 텍스트입니다. 안녕하세요."
        result = self.detector.detect(text)

        assert result.primary_language == Language.KOREAN
        assert result.script_detected == "hangul"

    def test_detect_arabic(self):
        """Test detection of Arabic text."""
        text = "هذا نص باللغة العربية. مرحبا بالعالم."
        result = self.detector.detect(text)

        assert result.primary_language == Language.ARABIC
        assert result.script_detected == "arabic"

    def test_detect_empty_text(self):
        """Test detection of empty text."""
        result = self.detector.detect("")

        assert result.primary_language == Language.UNKNOWN
        assert result.confidence == 0.0

    def test_detect_whitespace_only(self):
        """Test detection of whitespace-only text."""
        result = self.detector.detect("   \n\t  ")

        assert result.primary_language == Language.UNKNOWN

    def test_all_scores_populated(self):
        """Test that all language scores are populated."""
        text = "The quick brown fox"
        result = self.detector.detect(text)

        assert len(result.all_scores) > 0

    def test_multilingual_detection(self):
        """Test detection of multilingual content."""
        text = "Hello world. Hola mundo. Bonjour le monde."
        result = self.detector.detect(text)

        # Should detect multiple languages
        assert isinstance(result.is_multilingual, bool)
        assert isinstance(result.secondary_languages, list)

    def test_get_supported_languages(self):
        """Test getting list of supported languages."""
        languages = self.detector.get_supported_languages()

        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "en" in languages
        assert "es" in languages
        assert "unknown" not in languages

    def test_singleton_instance(self):
        """Test singleton pattern."""
        detector1 = get_language_detector()
        detector2 = get_language_detector()

        assert detector1 is detector2


class TestMultiLanguageProcessor:
    """Test multi-language processing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = MultiLanguageProcessor()

    def test_process_english_document(self):
        """Test processing English document."""
        text = """
        The invoice number is INV-001.
        The date of this invoice is January 15, 2024.
        The total amount due is $500.00.
        Please pay by the due date to avoid late fees.
        """
        fields = ["invoice_number", "date", "total"]
        result = self.processor.process_multilingual(text, fields)

        assert "language" in result
        assert result["language"] == "en"
        assert "fields" in result

    def test_process_spanish_document(self):
        """Test processing Spanish document."""
        text = """
        El número de factura es FACT-001.
        La fecha de esta factura es 15 de enero de 2024.
        El total que debe pagar es $500.00.
        Por favor pague antes de la fecha para evitar cargos.
        """
        fields = ["invoice_number", "date", "total"]
        result = self.processor.process_multilingual(text, fields)

        assert result["language"] == "es"

    def test_get_field_pattern(self):
        """Test getting localized field pattern."""
        pattern_en = self.processor.get_field_pattern("invoice_number", Language.ENGLISH)
        pattern_es = self.processor.get_field_pattern("invoice_number", Language.SPANISH)

        assert pattern_en == "invoice number"
        assert pattern_es == "número de factura"

    def test_get_field_pattern_unknown(self):
        """Test getting pattern for unknown field."""
        pattern = self.processor.get_field_pattern("unknown_field", Language.ENGLISH)

        assert pattern is None

    def test_singleton_instance(self):
        """Test singleton pattern."""
        processor1 = get_multi_language_processor()
        processor2 = get_multi_language_processor()

        assert processor1 is processor2


class TestLanguageEnum:
    """Test Language enum."""

    def test_all_languages_defined(self):
        """Test that all languages are properly defined."""
        assert Language.ENGLISH.value == "en"
        assert Language.SPANISH.value == "es"
        assert Language.FRENCH.value == "fr"
        assert Language.GERMAN.value == "de"
        assert Language.ITALIAN.value == "it"
        assert Language.PORTUGUESE.value == "pt"
        assert Language.RUSSIAN.value == "ru"
        assert Language.CHINESE.value == "zh"
        assert Language.JAPANESE.value == "ja"
        assert Language.KOREAN.value == "ko"
        assert Language.ARABIC.value == "ar"
        assert Language.UNKNOWN.value == "unknown"

    def test_language_count(self):
        """Test total number of supported languages."""
        # Should have many languages plus UNKNOWN
        assert len(Language) >= 20
