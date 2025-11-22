"""
Schema-based field extraction with JSON schema validation.
"""
import re
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from utils.logger import app_logger


@dataclass
class ExtractionResult:
    """Result of schema-based extraction."""
    field_name: str
    value: Any
    confidence: float
    valid: bool
    errors: List[str]


class SchemaExtractor:
    """
    Extract and validate fields based on JSON schema definitions.
    """

    def __init__(self):
        self.type_patterns = {
            "string": r".+",
            "number": r"-?\d+\.?\d*",
            "integer": r"-?\d+",
            "boolean": r"(?:true|false|yes|no|1|0)",
            "date": r"\d{1,4}[-/]\d{1,2}[-/]\d{1,4}",
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "phone": r"[\d\s\-\+\(\)]{7,20}",
            "currency": r"[\$€£¥]?\s*[\d,]+\.?\d*",
        }

    def extract(
        self,
        text: str,
        schema: Dict[str, Any]
    ) -> Dict[str, ExtractionResult]:
        """
        Extract fields from text based on JSON schema.

        Args:
            text: OCR text to extract from
            schema: JSON schema defining fields

        Returns:
            Dict of field name -> ExtractionResult
        """
        results = {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for field_name, field_schema in properties.items():
            result = self._extract_field(text, field_name, field_schema)

            # Check required
            if field_name in required and not result.value:
                result.valid = False
                result.errors.append(f"Required field '{field_name}' not found")

            results[field_name] = result

        return results

    def _extract_field(
        self,
        text: str,
        field_name: str,
        field_schema: Dict[str, Any]
    ) -> ExtractionResult:
        """Extract a single field based on its schema."""
        field_type = field_schema.get("type", "string")
        pattern = field_schema.get("pattern")
        enum_values = field_schema.get("enum")
        description = field_schema.get("description", "")

        value = None
        confidence = 0.0
        errors = []

        # Build search patterns
        search_patterns = self._build_search_patterns(
            field_name, description, field_type, pattern
        )

        # Search for value
        for search_pattern, weight in search_patterns:
            try:
                match = re.search(search_pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    extracted = match.group(1) if match.groups() else match.group(0)
                    extracted = extracted.strip()

                    # Validate and convert
                    validated, conv_value = self._validate_value(
                        extracted, field_type, field_schema
                    )

                    if validated:
                        value = conv_value
                        confidence = weight
                        break
                    else:
                        errors.append(f"Value '{extracted}' doesn't match type '{field_type}'")

            except re.error as e:
                errors.append(f"Pattern error: {e}")

        # Check enum constraint
        if value and enum_values and value not in enum_values:
            errors.append(f"Value '{value}' not in allowed values: {enum_values}")
            value = None

        # Check format constraints
        if value:
            format_errors = self._validate_format(value, field_schema)
            errors.extend(format_errors)

        return ExtractionResult(
            field_name=field_name,
            value=value,
            confidence=confidence,
            valid=len(errors) == 0 and value is not None,
            errors=errors
        )

    def _build_search_patterns(
        self,
        field_name: str,
        description: str,
        field_type: str,
        custom_pattern: str = None
    ) -> List[tuple]:
        """Build search patterns with confidence weights."""
        patterns = []
        value_pattern = self.type_patterns.get(field_type, r".+?")

        if custom_pattern:
            patterns.append((custom_pattern, 0.95))

        # Field name variations
        name_variations = [
            field_name.replace("_", " "),
            field_name.replace("_", ""),
            field_name,
        ]

        # Add description words
        if description:
            desc_words = description.split()[:3]
            name_variations.extend(desc_words)

        for name in name_variations:
            # Label: Value patterns
            patterns.append(
                (rf"{name}\s*[:\-=]\s*({value_pattern})", 0.9)
            )
            # Value after label on new line
            patterns.append(
                (rf"{name}\s*\n\s*({value_pattern})", 0.85)
            )

        # Generic type pattern as fallback
        patterns.append((f"({value_pattern})", 0.5))

        return patterns

    def _validate_value(
        self,
        value: str,
        field_type: str,
        schema: Dict[str, Any]
    ) -> tuple:
        """Validate and convert value to correct type."""
        try:
            if field_type == "integer":
                return True, int(re.sub(r"[^\d-]", "", value))

            elif field_type == "number":
                clean = re.sub(r"[^\d.-]", "", value)
                return True, float(clean)

            elif field_type == "boolean":
                lower = value.lower()
                if lower in ["true", "yes", "1"]:
                    return True, True
                elif lower in ["false", "no", "0"]:
                    return True, False
                return False, None

            elif field_type == "array":
                # Try to parse as JSON array or split by comma
                try:
                    return True, json.loads(value)
                except:
                    return True, [v.strip() for v in value.split(",")]

            else:  # string
                min_len = schema.get("minLength", 0)
                max_len = schema.get("maxLength", float("inf"))

                if min_len <= len(value) <= max_len:
                    return True, value
                return False, None

        except (ValueError, TypeError):
            return False, None

    def _validate_format(
        self,
        value: Any,
        schema: Dict[str, Any]
    ) -> List[str]:
        """Validate value against schema format constraints."""
        errors = []

        # String constraints
        if isinstance(value, str):
            if "minLength" in schema and len(value) < schema["minLength"]:
                errors.append(f"Value too short (min: {schema['minLength']})")
            if "maxLength" in schema and len(value) > schema["maxLength"]:
                errors.append(f"Value too long (max: {schema['maxLength']})")

        # Number constraints
        if isinstance(value, (int, float)):
            if "minimum" in schema and value < schema["minimum"]:
                errors.append(f"Value below minimum ({schema['minimum']})")
            if "maximum" in schema and value > schema["maximum"]:
                errors.append(f"Value above maximum ({schema['maximum']})")

        return errors

    def to_dict(
        self,
        results: Dict[str, ExtractionResult]
    ) -> Dict[str, Any]:
        """Convert results to simple dict of values."""
        return {
            name: result.value
            for name, result in results.items()
            if result.value is not None
        }

    def get_validation_report(
        self,
        results: Dict[str, ExtractionResult]
    ) -> Dict[str, Any]:
        """Generate validation report."""
        total = len(results)
        valid = sum(1 for r in results.values() if r.valid)
        errors = []

        for name, result in results.items():
            if result.errors:
                errors.append({
                    "field": name,
                    "errors": result.errors
                })

        return {
            "total_fields": total,
            "valid_fields": valid,
            "invalid_fields": total - valid,
            "success_rate": round((valid / total * 100) if total > 0 else 0, 2),
            "errors": errors
        }


# Predefined schemas for common document types
INVOICE_SCHEMA = {
    "type": "object",
    "required": ["invoice_number", "total_amount"],
    "properties": {
        "invoice_number": {
            "type": "string",
            "description": "Invoice number or ID",
            "pattern": r"(?:invoice|inv|#)\s*[:\-]?\s*([A-Z0-9\-]+)"
        },
        "invoice_date": {
            "type": "string",
            "description": "Invoice date",
            "pattern": r"(?:date|dated)\s*[:\-]?\s*(\d{1,4}[-/]\d{1,2}[-/]\d{1,4})"
        },
        "due_date": {
            "type": "string",
            "description": "Payment due date"
        },
        "vendor_name": {
            "type": "string",
            "description": "Vendor or supplier name"
        },
        "total_amount": {
            "type": "number",
            "description": "Total invoice amount",
            "minimum": 0,
            "pattern": r"(?:total|amount|sum|due)\s*[:\-]?\s*[\$€£]?\s*([\d,]+\.?\d*)"
        },
        "tax_amount": {
            "type": "number",
            "description": "Tax amount",
            "minimum": 0,
            "pattern": r"(?:tax|vat|gst)\s*[:\-]?\s*[\$€£]?\s*([\d,]+\.?\d*)"
        },
        "currency": {
            "type": "string",
            "enum": ["USD", "EUR", "GBP", "JPY", "CAD", "AUD"]
        }
    }
}

RECEIPT_SCHEMA = {
    "type": "object",
    "required": ["total_amount"],
    "properties": {
        "store_name": {
            "type": "string",
            "description": "Store or merchant name"
        },
        "date": {
            "type": "string",
            "description": "Transaction date"
        },
        "total_amount": {
            "type": "number",
            "description": "Total amount",
            "minimum": 0
        },
        "payment_method": {
            "type": "string",
            "enum": ["cash", "credit", "debit", "check"]
        },
        "receipt_number": {
            "type": "string"
        }
    }
}


# Global instance
schema_extractor = SchemaExtractor()


if __name__ == "__main__":
    print("=" * 60)
    print("SCHEMA EXTRACTOR TEST")
    print("=" * 60)

    sample_text = """
    INVOICE

    Invoice Number: INV-2024-001
    Date: 2024-01-15

    Bill To:
    Acme Corporation

    Total Amount: $1,234.56
    Tax: $98.76
    Currency: USD
    """

    extractor = SchemaExtractor()
    results = extractor.extract(sample_text, INVOICE_SCHEMA)

    print("\nExtracted fields:")
    for name, result in results.items():
        status = "✓" if result.valid else "✗"
        print(f"  {status} {name}: {result.value} (confidence: {result.confidence:.0%})")

    report = extractor.get_validation_report(results)
    print(f"\nValidation: {report['valid_fields']}/{report['total_fields']} valid")

    print("=" * 60)
