"""
Enhanced structured output processor for OCR results.
Combines classification, extraction, and parsing into a unified output format.
"""
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from core.document_classifier import get_document_classifier, DocumentType
from core.semantic_extractor import get_semantic_extractor
from core.language_support import get_language_detector
from core.field_extractor import FieldExtractor
from core.output_parser import OutputParser


@dataclass
class LineItem:
    """A line item from a table."""
    description: str
    quantity: Optional[str] = None
    rate: Optional[str] = None
    amount: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None


@dataclass
class StructuredOutput:
    """Enhanced structured output from OCR processing."""
    document_type: str
    confidence: float
    language: str
    extracted_fields: Dict[str, Any]
    line_items: List[Dict]
    entities: List[Dict]
    raw: Dict[str, Any]


class StructuredOutputProcessor:
    """Process OCR results into structured, usable format."""

    def __init__(self):
        """Initialize the processor with all components."""
        self.classifier = get_document_classifier()
        self.semantic_extractor = get_semantic_extractor()
        self.language_detector = get_language_detector()
        self.field_extractor = FieldExtractor()
        self.output_parser = OutputParser()

    def process(self, text: str, tables_html: List[str] = None) -> Dict[str, Any]:
        """
        Process OCR text into structured output.

        Args:
            text: Raw OCR text
            tables_html: Optional list of HTML tables

        Returns:
            Structured output dictionary
        """
        # Classify document
        classification = self.classifier.classify(text)

        # Detect language
        language = self.language_detector.detect(text)

        # Extract fields based on document type
        extracted_fields = self._extract_fields(text, classification.document_type)

        # Extract entities
        semantic_result = self.semantic_extractor.extract(text)
        entities = semantic_result.entities

        # Parse line items from tables
        line_items = []
        if tables_html:
            for table in tables_html:
                items = self._parse_line_items(table)
                line_items.extend(items)

        # Build raw data
        parsed = self.output_parser.parse(text)
        raw = {
            "text": text,
            "tables_html": tables_html or [],
            "pages": [asdict(p) for p in parsed.pages] if parsed.pages else []
        }

        return {
            "document_type": classification.document_type.value,
            "confidence": round(classification.confidence, 2),
            "language": language.primary_language.value,
            "extracted_fields": extracted_fields,
            "line_items": line_items,
            "entities": entities,
            "raw": raw
        }

    def _extract_fields(self, text: str, doc_type: DocumentType) -> Dict[str, Any]:
        """Extract fields based on document type."""
        fields = {}

        # Common patterns for all documents
        common_patterns = {
            "date": [
                r"(?:Date|Dated?)\s*:?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
                r"(?:Date|Dated?)\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            ],
            "total": [
                r"(?:Total|Grand Total|Amount Due|Balance Due)\s*:?\s*\*?\*?\s*\$?([\d,]+\.?\d*)",
            ],
        }

        # Document-specific patterns
        doc_patterns = {
            DocumentType.INVOICE: {
                "invoice_number": [
                    r"(?:Invoice|INV)\s*#?\s*:?\s*(\w+)",
                    r"#\s*(\d+)",
                ],
                "bill_to": [
                    r"Bill\s+To\s*:?\s*\*?\*?([^*\n]+?)(?:\n\n|\nShip)",
                    r"Bill\s+To\s*:?\s*\*?\*?\s*([A-Za-z][A-Za-z\s]+?)(?:\n|Ship)",
                ],
                "ship_to": [
                    r"Ship\s+To\s*:?\s*\*?\*?\s*([^\n]+)",
                ],
                "subtotal": [
                    r"Subtotal\s*:?\s*\$?([\d,]+\.?\d*)",
                ],
                "discount": [
                    r"Discount\s*(?:\([^)]+\))?\s*:?\s*\$?([\d,]+\.?\d*)",
                ],
                "tax": [
                    r"Tax\s*(?:\([^)]+\))?\s*:?\s*\$?([\d,]+\.?\d*)",
                ],
                "shipping": [
                    r"Shipping\s*:?\s*\$?([\d,]+\.?\d*)",
                ],
                "ship_mode": [
                    r"Ship\s+Mode\s*:?\s*([^\n]+)",
                ],
                "order_id": [
                    r"Order\s+ID\s*:?\s*([^\n]+)",
                ],
                "notes": [
                    r"Notes\s*:?\s*([^\n]+)",
                ],
                "terms": [
                    r"Terms\s*:?\s*([^\n]+)",
                ],
            },
            DocumentType.RECEIPT: {
                "receipt_number": [
                    r"(?:Receipt|Transaction)\s*#?\s*:?\s*(\w+)",
                ],
                "store": [
                    r"^([A-Za-z\s]+?)(?:\n|Receipt)",
                ],
                "cashier": [
                    r"Cashier\s*:?\s*([^\n]+)",
                ],
                "payment_method": [
                    r"(?:Paid|Payment)\s+(?:by|via)\s*:?\s*([^\n]+)",
                ],
            },
            DocumentType.CONTRACT: {
                "contract_date": [
                    r"(?:dated?|entered into)\s+(?:as of\s+)?([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
                ],
                "parties": [
                    r"(?:between|parties?)\s*:?\s*([^\n]+)",
                ],
                "effective_date": [
                    r"effective\s+(?:date)?\s*:?\s*([^\n]+)",
                ],
            },
            DocumentType.BANK_STATEMENT: {
                "account_number": [
                    r"(?:Account|Acct)\s*#?\s*:?\s*([X\d\-]+)",
                    r"Account\s+Number\s*:?\s*([^\n]+)",
                ],
                "statement_period": [
                    r"(?:Statement\s+Period|Period)\s*:?\s*([^\n]+)",
                ],
                "opening_balance": [
                    r"(?:Opening|Beginning)\s+Balance\s*:?\s*\$?([\d,]+\.?\d*)",
                ],
                "closing_balance": [
                    r"(?:Closing|Ending)\s+Balance\s*:?\s*\$?([\d,]+\.?\d*)",
                ],
                "total_deposits": [
                    r"(?:Total\s+)?Deposits\s*:?\s*\$?([\d,]+\.?\d*)",
                ],
                "total_withdrawals": [
                    r"(?:Total\s+)?Withdrawals\s*:?\s*\$?([\d,]+\.?\d*)",
                ],
            },
            DocumentType.ID_DOCUMENT: {
                "document_number": [
                    r"(?:ID|License|Passport)\s*#?\s*:?\s*([A-Z0-9\-]+)",
                    r"(?:Number|No\.?)\s*:?\s*([A-Z0-9\-]+)",
                ],
                "full_name": [
                    r"(?:Name|Full\s+Name)\s*:?\s*([A-Za-z\s]+)",
                ],
                "date_of_birth": [
                    r"(?:DOB|Date\s+of\s+Birth|Birth\s+Date)\s*:?\s*([^\n]+)",
                ],
                "expiration_date": [
                    r"(?:Exp|Expires?|Expiration)\s*:?\s*([^\n]+)",
                ],
                "issue_date": [
                    r"(?:Issued?|Issue\s+Date)\s*:?\s*([^\n]+)",
                ],
                "address": [
                    r"(?:Address|Addr)\s*:?\s*([^\n]+)",
                ],
            },
            DocumentType.MEDICAL: {
                "patient_name": [
                    r"(?:Patient|Name)\s*:?\s*([A-Za-z\s]+)",
                ],
                "patient_id": [
                    r"(?:Patient|Medical)\s*(?:ID|#)\s*:?\s*([^\n]+)",
                    r"MRN\s*:?\s*([^\n]+)",
                ],
                "provider": [
                    r"(?:Provider|Physician|Doctor)\s*:?\s*([^\n]+)",
                ],
                "diagnosis": [
                    r"(?:Diagnosis|Dx)\s*:?\s*([^\n]+)",
                ],
                "visit_date": [
                    r"(?:Visit|Service)\s+Date\s*:?\s*([^\n]+)",
                ],
                "facility": [
                    r"(?:Facility|Hospital|Clinic)\s*:?\s*([^\n]+)",
                ],
            },
            DocumentType.TAX_DOCUMENT: {
                "tax_year": [
                    r"(?:Tax\s+Year|Year)\s*:?\s*(\d{4})",
                ],
                "form_type": [
                    r"Form\s+(\d+[A-Z\-]*)",
                ],
                "taxpayer_name": [
                    r"(?:Taxpayer|Name)\s*:?\s*([^\n]+)",
                ],
                "ssn": [
                    r"(?:SSN|Social\s+Security)\s*:?\s*([X\d\-]+)",
                ],
                "gross_income": [
                    r"(?:Gross\s+Income|Total\s+Income)\s*:?\s*\$?([\d,]+\.?\d*)",
                ],
                "tax_due": [
                    r"(?:Tax\s+Due|Amount\s+Owed)\s*:?\s*\$?([\d,]+\.?\d*)",
                ],
                "refund": [
                    r"(?:Refund|Amount\s+Refunded)\s*:?\s*\$?([\d,]+\.?\d*)",
                ],
            },
        }

        # Extract common fields
        for field_name, patterns in common_patterns.items():
            value = self._extract_first_match(text, patterns)
            if value:
                fields[field_name] = value.strip()

        # Extract document-specific fields
        if doc_type in doc_patterns:
            for field_name, patterns in doc_patterns[doc_type].items():
                value = self._extract_first_match(text, patterns)
                if value:
                    # Clean up the value
                    cleaned = value.strip().strip('*').strip()
                    if cleaned:
                        fields[field_name] = cleaned

        # Post-process nested fields
        fields = self._structure_nested_fields(fields)

        return fields

    def _extract_first_match(self, text: str, patterns: List[str]) -> Optional[str]:
        """Extract first matching value from patterns."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1)
        return None

    def _structure_nested_fields(self, fields: Dict) -> Dict:
        """Structure flat fields into nested objects where appropriate."""
        result = {}

        for key, value in fields.items():
            if key == "bill_to":
                result["bill_to"] = {"name": value}
            elif key == "ship_to":
                result["ship_to"] = {"location": value}
            else:
                result[key] = value

        return result

    def _parse_line_items(self, table_html: str) -> List[Dict]:
        """Parse line items from HTML table."""
        from bs4 import BeautifulSoup

        items = []
        soup = BeautifulSoup(table_html, 'html.parser')

        # Find all rows
        rows = soup.find_all('tr')
        if len(rows) < 2:
            return items

        # Get headers
        header_row = rows[0]
        headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]

        # Parse data rows
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) != len(headers):
                continue

            item = {}
            for i, cell in enumerate(cells):
                header = headers[i] if i < len(headers) else f"col_{i}"
                cell_text = cell.get_text(strip=True)

                # Map common column names
                if header in ['item', 'description', 'product']:
                    # Parse description, may contain category/SKU
                    desc_parts = cell_text.split('\n')
                    item['description'] = desc_parts[0].strip()
                    if len(desc_parts) > 1:
                        # Try to extract category and SKU
                        extra = desc_parts[1] if len(desc_parts) > 1 else ""
                        sku_match = re.search(r'([A-Z]+-[A-Z]+-\d+)', extra)
                        if sku_match:
                            item['sku'] = sku_match.group(1)
                            category = extra.replace(sku_match.group(1), '').strip().strip(',').strip()
                            if category:
                                item['category'] = category
                elif header in ['quantity', 'qty']:
                    item['quantity'] = cell_text
                elif header in ['rate', 'price', 'unit price']:
                    item['rate'] = cell_text
                elif header in ['amount', 'total', 'subtotal']:
                    item['amount'] = cell_text

            if item.get('description'):
                items.append(item)

        return items


# Singleton instance
_processor = None


def get_structured_processor() -> StructuredOutputProcessor:
    """Get the structured output processor singleton."""
    global _processor
    if _processor is None:
        _processor = StructuredOutputProcessor()
    return _processor


def process_to_structured(text: str, tables_html: List[str] = None) -> Dict[str, Any]:
    """
    Convenience function to process text to structured output.

    Args:
        text: Raw OCR text
        tables_html: Optional list of HTML tables

    Returns:
        Structured output dictionary
    """
    processor = get_structured_processor()
    return processor.process(text, tables_html)
