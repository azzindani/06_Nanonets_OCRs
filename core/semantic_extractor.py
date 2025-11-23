"""
Semantic field extraction using LLM capabilities.
"""
import re
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class SemanticField:
    """A semantically extracted field."""
    name: str
    value: Any
    confidence: float
    context: str
    reasoning: str


@dataclass
class SemanticExtractionResult:
    """Result of semantic extraction."""
    fields: Dict[str, SemanticField]
    summary: str
    entities: List[Dict[str, str]]
    key_points: List[str]


class SemanticExtractor:
    """
    Extract fields semantically using natural language understanding.

    This extractor uses pattern matching and heuristics to understand
    document context and extract fields based on meaning rather than
    just keyword matching.
    """

    def __init__(self):
        """Initialize the semantic extractor."""
        self._entity_patterns = self._build_entity_patterns()
        self._context_patterns = self._build_context_patterns()

    def _build_entity_patterns(self) -> Dict[str, List[str]]:
        """Build patterns for entity extraction."""
        # Common document labels to exclude from person detection
        self._person_exclusions = {
            'bill to', 'ship to', 'sold to', 'deliver to', 'ship mode', 'second class',
            'first class', 'standard class', 'balance due', 'amount due', 'total due',
            'grand total', 'sub total', 'thank you', 'terms and', 'notes and',
            'order id', 'invoice number', 'receipt number', 'customer id',
        }
        return {
            "person": [
                r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b",  # Names
                r"(?:Mr\.|Mrs\.|Ms\.|Dr\.)\s+[A-Z][a-z]+",
            ],
            "organization": [
                r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc\.|Corp\.|LLC|Ltd\.)",
                r"[A-Z]{2,}\s+(?:Corporation|Company|Industries)",
            ],
            "date": [
                r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
                r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
                r"\d{4}-\d{2}-\d{2}",
            ],
            "money": [
                r"\$[\d,]+\.?\d*",
                r"[\d,]+\.?\d*\s*(?:USD|EUR|GBP)",
                r"(?:€|£|¥)[\d,]+\.?\d*",
            ],
            "email": [
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            ],
            "phone": [
                r"\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
                r"\(\d{3}\)\s*\d{3}-\d{4}",
            ],
            "address": [
                r"\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)",
            ],
        }

    def _build_context_patterns(self) -> Dict[str, Dict]:
        """Build context-aware extraction patterns."""
        return {
            "payment_info": {
                "triggers": ["payment", "pay", "due", "amount", "total"],
                "extract": {
                    "amount": r"(?:total|amount|due|payment)\s*:?\s*\$?([\d,]+\.?\d*)",
                    "due_date": r"(?:due|payment)\s+(?:date|by)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                    "method": r"(?:pay|payment)\s+(?:by|via|method)\s*:?\s*(\w+)",
                }
            },
            "contact_info": {
                "triggers": ["contact", "phone", "email", "address", "reach"],
                "extract": {
                    "phone": r"(?:phone|tel|call)\s*:?\s*([\d\s\-\(\)]+)",
                    "email": r"(?:email|e-mail)\s*:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                    "address": r"(?:address|location)\s*:?\s*(.+?)(?:\n|$)",
                }
            },
            "identification": {
                "triggers": ["id", "number", "reference", "account"],
                "extract": {
                    "id_number": r"(?:id|identification|account|reference)\s*(?:number|#|no)?\s*:?\s*([A-Z0-9\-]+)",
                    "customer_id": r"(?:customer|client)\s*(?:id|#)\s*:?\s*([A-Z0-9\-]+)",
                }
            },
            "dates": {
                "triggers": ["date", "issued", "effective", "expires"],
                "extract": {
                    "issue_date": r"(?:issue|issued|created)\s+(?:date)?\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                    "effective_date": r"(?:effective|start)\s+(?:date)?\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                    "expiry_date": r"(?:expir|end)\w*\s+(?:date)?\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                }
            }
        }

    def extract(
        self,
        text: str,
        queries: Optional[List[str]] = None,
        context: Optional[str] = None
    ) -> SemanticExtractionResult:
        """
        Extract fields semantically from text.

        Args:
            text: The document text to extract from.
            queries: Natural language queries for specific fields.
            context: Additional context about the document.

        Returns:
            SemanticExtractionResult with extracted fields and metadata.
        """
        text_lower = text.lower()
        fields: Dict[str, SemanticField] = {}
        entities: List[Dict[str, str]] = []

        # Extract named entities
        for entity_type, patterns in self._entity_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    # Filter out false positives for person entities
                    if entity_type == "person":
                        match_lower = match.lower()
                        if match_lower in self._person_exclusions:
                            continue
                        # Also skip if it contains common product words
                        if any(word in match_lower for word in ['inkjet', 'laser', 'printer', 'machine', 'class']):
                            continue
                    entities.append({
                        "type": entity_type,
                        "value": match,
                        "confidence": 0.8
                    })

        # Context-aware extraction
        for context_name, config in self._context_patterns.items():
            # Check if context is relevant
            if any(trigger in text_lower for trigger in config["triggers"]):
                for field_name, pattern in config["extract"].items():
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        fields[field_name] = SemanticField(
                            name=field_name,
                            value=value,
                            confidence=0.85,
                            context=context_name,
                            reasoning=f"Found in {context_name} context with pattern match"
                        )

        # Process natural language queries
        if queries:
            for query in queries:
                field = self._extract_from_query(text, query)
                if field:
                    fields[field.name] = field

        # Generate summary
        summary = self._generate_summary(text, entities)

        # Extract key points
        key_points = self._extract_key_points(text)

        return SemanticExtractionResult(
            fields=fields,
            summary=summary,
            entities=entities[:20],  # Limit entities
            key_points=key_points
        )

    def _extract_from_query(self, text: str, query: str) -> Optional[SemanticField]:
        """
        Extract a field based on a natural language query.

        Args:
            text: The document text.
            query: Natural language query like "What is the invoice total?"

        Returns:
            SemanticField if found, None otherwise.
        """
        query_lower = query.lower()

        # Identify what we're looking for
        field_mappings = {
            "total": r"total\s*:?\s*\$?([\d,]+\.?\d*)",
            "date": r"date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            "name": r"(?:name|from|to)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            "number": r"(?:number|#|no)\s*:?\s*([A-Z0-9\-]+)",
            "amount": r"(?:amount|sum|price)\s*:?\s*\$?([\d,]+\.?\d*)",
            "address": r"address\s*:?\s*(.+?)(?:\n|$)",
            "email": r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            "phone": r"(\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
        }

        for key, pattern in field_mappings.items():
            if key in query_lower:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return SemanticField(
                        name=key,
                        value=match.group(1).strip(),
                        confidence=0.75,
                        context="query",
                        reasoning=f"Extracted based on query: {query}"
                    )

        return None

    def _generate_summary(self, text: str, entities: List[Dict]) -> str:
        """Generate a brief summary of the document."""
        # Count entity types
        entity_counts = {}
        for entity in entities:
            etype = entity["type"]
            entity_counts[etype] = entity_counts.get(etype, 0) + 1

        # Build summary
        parts = []

        if "organization" in entity_counts:
            parts.append(f"{entity_counts['organization']} organization(s)")
        if "person" in entity_counts:
            parts.append(f"{entity_counts['person']} person(s)")
        if "money" in entity_counts:
            parts.append(f"{entity_counts['money']} monetary value(s)")
        if "date" in entity_counts:
            parts.append(f"{entity_counts['date']} date(s)")

        if parts:
            return f"Document contains: {', '.join(parts)}."
        else:
            word_count = len(text.split())
            return f"Document with {word_count} words."

    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from the document."""
        key_points = []

        # Look for bullet points or numbered items
        bullet_pattern = r"(?:^|\n)\s*(?:[\•\-\*]|\d+\.)\s*(.+?)(?:\n|$)"
        bullets = re.findall(bullet_pattern, text)
        key_points.extend(bullets[:5])

        # Look for important sentences
        important_patterns = [
            r"(?:important|note|attention|warning)\s*:?\s*(.+?)(?:\n|$)",
            r"(?:please|must|required)\s+(.+?)(?:\n|$)",
        ]

        for pattern in important_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            key_points.extend(matches[:2])

        return key_points[:10]

    def extract_with_schema(
        self,
        text: str,
        schema: Dict[str, Dict]
    ) -> Dict[str, SemanticField]:
        """
        Extract fields based on a provided schema.

        Args:
            text: The document text.
            schema: Schema defining fields to extract.

        Returns:
            Dictionary of extracted SemanticFields.
        """
        fields = {}

        for field_name, field_config in schema.items():
            field_type = field_config.get("type", "string")
            description = field_config.get("description", "")

            # Use description to guide extraction
            if description:
                field = self._extract_from_query(text, description)
                if field:
                    field.name = field_name
                    fields[field_name] = field

        return fields


# Singleton instance
_semantic_extractor = None


def get_semantic_extractor() -> SemanticExtractor:
    """Get the semantic extractor singleton."""
    global _semantic_extractor
    if _semantic_extractor is None:
        _semantic_extractor = SemanticExtractor()
    return _semantic_extractor
