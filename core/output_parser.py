"""
Output parser for extracting structured data from raw OCR output.
"""
import re
import io
from dataclasses import dataclass, field
from typing import List, Dict, Any

from bs4 import BeautifulSoup
import pandas as pd


@dataclass
class Table:
    """Extracted table data."""
    html: str
    csv: str
    page_number: int
    table_index: int


@dataclass
class ParsedPage:
    """Parsed data from a single page."""
    page_number: int
    raw_text: str
    tables_html: List[str] = field(default_factory=list)
    tables_csv: List[str] = field(default_factory=list)
    latex_equations: List[str] = field(default_factory=list)
    image_descriptions: List[str] = field(default_factory=list)
    watermarks: List[str] = field(default_factory=list)
    page_numbers_extracted: List[str] = field(default_factory=list)
    checkboxes: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ParsedOutput:
    """Complete parsed output from OCR."""
    pages: List[ParsedPage]


class OutputParser:
    """
    Parses raw OCR output into structured components.
    """

    def parse(self, raw_output: str) -> ParsedOutput:
        """
        Parse raw OCR output into structured data.

        Args:
            raw_output: Raw text from OCR processing.

        Returns:
            ParsedOutput with structured data.
        """
        pages_raw = re.split(r'\n--- Page \d+ ---\n', raw_output)
        pages_raw = [p.strip() for p in pages_raw if p.strip()]

        parsed_pages = []

        for page_idx, page_text in enumerate(pages_raw):
            page_data = self._parse_page(page_text, page_idx + 1)
            parsed_pages.append(page_data)

        return ParsedOutput(pages=parsed_pages)

    def _parse_page(self, page_text: str, page_number: int) -> ParsedPage:
        """Parse a single page of text."""
        page_data = ParsedPage(
            page_number=page_number,
            raw_text=page_text
        )

        # Extract HTML tables
        page_data.tables_html, page_data.tables_csv = self.extract_tables(page_text)

        # Extract LaTeX equations
        page_data.latex_equations = self.extract_equations(page_text)

        # Extract image descriptions
        page_data.image_descriptions = self.extract_images(page_text)

        # Extract watermarks
        page_data.watermarks = self.extract_watermarks(page_text)

        # Extract page numbers
        page_data.page_numbers_extracted = self.extract_page_numbers(page_text)

        # Extract checkboxes
        page_data.checkboxes = self.extract_checkboxes(page_text)

        return page_data

    def extract_tables(self, content: str) -> tuple:
        """
        Extract HTML tables and convert to CSV.

        Args:
            content: Text content to parse.

        Returns:
            Tuple of (html_tables, csv_tables).
        """
        soup = BeautifulSoup(content, 'html.parser')
        tables = soup.find_all('table')

        html_tables = []
        csv_tables = []

        for table_tag in tables:
            table_html = str(table_tag)
            html_tables.append(table_html)

            # Convert to CSV
            try:
                df = pd.read_html(io.StringIO(table_html))[0]
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                csv_tables.append(csv_buffer.getvalue())
            except Exception as e:
                csv_tables.append(f"Error converting table to CSV: {e}")

        return html_tables, csv_tables

    def extract_equations(self, content: str) -> List[str]:
        """
        Extract LaTeX equations from content.

        Args:
            content: Text content to parse.

        Returns:
            List of LaTeX equation strings.
        """
        equations = []

        # Match inline and display math
        patterns = [
            r'\$\$([^$]+)\$\$',  # Display math
            r'\$([^$]+)\$',  # Inline math
            r'\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}',
            r'\\begin\{align\*?\}(.*?)\\end\{align\*?\}',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    for eq in match:
                        if eq.strip():
                            equations.append(eq.strip())
                elif match.strip():
                    equations.append(match.strip())

        return equations

    def extract_images(self, content: str) -> List[str]:
        """
        Extract image descriptions/captions.

        Args:
            content: Text content to parse.

        Returns:
            List of image descriptions.
        """
        matches = re.findall(r'<img>(.*?)</img>', content, re.DOTALL)
        return [img.strip() for img in matches if img.strip()]

    def extract_watermarks(self, content: str) -> List[str]:
        """
        Extract watermark text.

        Args:
            content: Text content to parse.

        Returns:
            List of watermark strings.
        """
        matches = re.findall(r'<watermark>(.*?)</watermark>', content)
        return [wm.strip() for wm in matches if wm.strip()]

    def extract_page_numbers(self, content: str) -> List[str]:
        """
        Extract page number markers.

        Args:
            content: Text content to parse.

        Returns:
            List of page number strings.
        """
        matches = re.findall(r'<page_number>(.*?)</page_number>', content)
        return [pn.strip() for pn in matches if pn.strip()]

    def extract_checkboxes(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract checkbox states.

        Args:
            content: Text content to parse.

        Returns:
            List of checkbox dictionaries with state.
        """
        checkboxes = []

        # Find checked boxes
        checked_pattern = r'☑\s*([^\n☐☑]*)'
        for match in re.finditer(checked_pattern, content):
            checkboxes.append({
                "checked": True,
                "label": match.group(1).strip()
            })

        # Find unchecked boxes
        unchecked_pattern = r'☐\s*([^\n☐☑]*)'
        for match in re.finditer(unchecked_pattern, content):
            checkboxes.append({
                "checked": False,
                "label": match.group(1).strip()
            })

        return checkboxes

    def to_dict(self, parsed: ParsedOutput) -> Dict[str, Any]:
        """
        Convert ParsedOutput to dictionary format.

        Args:
            parsed: ParsedOutput object.

        Returns:
            Dictionary representation.
        """
        return {
            "pages": [
                {
                    "page_number": page.page_number,
                    "raw_text": page.raw_text,
                    "tables_html": page.tables_html,
                    "tables_csv": page.tables_csv,
                    "latex_equations": page.latex_equations,
                    "image_descriptions": page.image_descriptions,
                    "watermarks": page.watermarks,
                    "page_numbers_extracted": page.page_numbers_extracted,
                    "checkboxes": page.checkboxes
                }
                for page in parsed.pages
            ]
        }


if __name__ == "__main__":
    print("=" * 60)
    print("OUTPUT PARSER MODULE TEST")
    print("=" * 60)

    parser = OutputParser()

    # Test with sample content
    sample = """
    --- Page 1 ---
    This is some text with a table:
    <table><tr><td>A</td><td>B</td></tr></table>

    And an equation: $E = mc^2$

    <img>A sample image description</img>

    <watermark>CONFIDENTIAL</watermark>

    ☑ Task completed
    ☐ Task pending
    """

    result = parser.parse(sample)
    print(f"  Pages parsed: {len(result.pages)}")

    if result.pages:
        page = result.pages[0]
        print(f"  Tables found: {len(page.tables_html)}")
        print(f"  Equations found: {len(page.latex_equations)}")
        print(f"  Images found: {len(page.image_descriptions)}")
        print(f"  Watermarks found: {len(page.watermarks)}")
        print(f"  Checkboxes found: {len(page.checkboxes)}")

    print(f"\n  ✓ Output parser tests passed")

    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
