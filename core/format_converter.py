"""
Format converter for converting parsed output to various formats.
"""
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, Any, List

from core.output_parser import ParsedOutput


class FormatConverter:
    """
    Converts parsed OCR output to various formats.
    """

    def to_json(self, parsed: ParsedOutput) -> str:
        """
        Convert parsed output to JSON string.

        Args:
            parsed: ParsedOutput object.

        Returns:
            JSON string.
        """
        data = self._to_dict(parsed)
        return json.dumps(data, indent=2)

    def to_xml(self, parsed: ParsedOutput) -> str:
        """
        Convert parsed output to XML string.

        Args:
            parsed: ParsedOutput object.

        Returns:
            XML string.
        """
        root = ET.Element("DocumentOCR")

        for page_data in parsed.pages:
            page_elem = ET.SubElement(
                root, "Page",
                number=str(page_data.page_number)
            )

            # Raw text
            ET.SubElement(page_elem, "RawText").text = page_data.raw_text

            # Tables
            if page_data.tables_html:
                tables_elem = ET.SubElement(page_elem, "Tables")
                for i, html_table in enumerate(page_data.tables_html):
                    table_elem = ET.SubElement(tables_elem, "Table", id=str(i + 1))
                    ET.SubElement(table_elem, "HTMLContent").text = html_table
                    if i < len(page_data.tables_csv):
                        ET.SubElement(table_elem, "CSVContent").text = page_data.tables_csv[i]

            # Equations
            if page_data.latex_equations:
                equations_elem = ET.SubElement(page_elem, "Equations")
                for i, eq in enumerate(page_data.latex_equations):
                    ET.SubElement(equations_elem, "Equation", id=str(i + 1)).text = eq

            # Images
            if page_data.image_descriptions:
                images_elem = ET.SubElement(page_elem, "Images")
                for i, desc in enumerate(page_data.image_descriptions):
                    ET.SubElement(images_elem, "Description", id=str(i + 1)).text = desc

            # Watermarks
            if page_data.watermarks:
                watermarks_elem = ET.SubElement(page_elem, "Watermarks")
                for i, wm in enumerate(page_data.watermarks):
                    ET.SubElement(watermarks_elem, "Watermark", id=str(i + 1)).text = wm

            # Page numbers
            if page_data.page_numbers_extracted:
                page_nums_elem = ET.SubElement(page_elem, "PageNumbers")
                for i, pn in enumerate(page_data.page_numbers_extracted):
                    ET.SubElement(page_nums_elem, "PageNumber", id=str(i + 1)).text = pn

            # Checkboxes
            if page_data.checkboxes:
                checkboxes_elem = ET.SubElement(page_elem, "Checkboxes")
                for i, cb in enumerate(page_data.checkboxes):
                    cb_elem = ET.SubElement(
                        checkboxes_elem, "Checkbox",
                        id=str(i + 1),
                        checked=str(cb.get("checked", False)).lower()
                    )
                    cb_elem.text = cb.get("label", "")

        # Pretty print
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def to_csv(self, parsed: ParsedOutput) -> str:
        """
        Convert parsed output tables to CSV format.

        Args:
            parsed: ParsedOutput object.

        Returns:
            Combined CSV string.
        """
        tables = []
        for page in parsed.pages:
            tables.extend(page.tables_csv)

        if not tables:
            return "No tables found or could not convert."

        output = []
        for i, table_csv in enumerate(tables):
            output.append(f"--- Table {i + 1} ---\n{table_csv}")

        return "\n\n".join(output)

    def to_html(self, parsed: ParsedOutput) -> str:
        """
        Convert parsed output to HTML preview.

        Args:
            parsed: ParsedOutput object.

        Returns:
            HTML string.
        """
        html_parts = [
            '<div style="font-family: Arial, sans-serif; padding: 20px; '
            'background: #f5f5f5; border-radius: 8px;">',
            '<h2 style="color: #333; border-bottom: 2px solid #4CAF50; '
            'padding-bottom: 10px;">📄 Document Preview</h2>'
        ]

        for page in parsed.pages:
            html_parts.append(
                f'<div style="background: white; padding: 15px; '
                f'border-radius: 5px; margin-top: 15px;">'
            )
            html_parts.append(f'<h3>Page {page.page_number}</h3>')

            # Raw text with line breaks
            text_html = page.raw_text.replace('\n', '<br>')
            html_parts.append(f'<div style="line-height: 1.6;">{text_html}</div>')

            html_parts.append('</div>')

        html_parts.append('</div>')

        return '\n'.join(html_parts)

    def _to_dict(self, parsed: ParsedOutput) -> Dict[str, Any]:
        """
        Convert ParsedOutput to dictionary.

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

    def get_all_tables_html(self, parsed: ParsedOutput) -> str:
        """
        Get all HTML tables from parsed output.

        Args:
            parsed: ParsedOutput object.

        Returns:
            Combined HTML tables string.
        """
        all_tables = []
        for page in parsed.pages:
            all_tables.extend(page.tables_html)

        if not all_tables:
            return "No HTML tables found."

        return "\n".join(all_tables)

    def get_all_equations(self, parsed: ParsedOutput) -> str:
        """
        Get all equations from parsed output.

        Args:
            parsed: ParsedOutput object.

        Returns:
            Combined equations string.
        """
        all_equations = []
        for page in parsed.pages:
            for i, eq in enumerate(page.latex_equations):
                all_equations.append(
                    f"--- Page {page.page_number}, Equation {i + 1} ---\n{eq}"
                )

        if not all_equations:
            return "No LaTeX equations found."

        return "\n\n".join(all_equations)


if __name__ == "__main__":
    print("=" * 60)
    print("FORMAT CONVERTER MODULE TEST")
    print("=" * 60)

    from core.output_parser import OutputParser

    # Create sample data
    parser = OutputParser()
    sample = """
    --- Page 1 ---
    Sample text with table:
    <table><tr><td>A</td><td>B</td></tr></table>

    Equation: $x^2 + y^2 = z^2$

    <img>Test image</img>
    """

    parsed = parser.parse(sample)
    converter = FormatConverter()

    # Test JSON conversion
    json_output = converter.to_json(parsed)
    print(f"  JSON output length: {len(json_output)} chars")

    # Test XML conversion
    xml_output = converter.to_xml(parsed)
    print(f"  XML output length: {len(xml_output)} chars")

    # Test HTML conversion
    html_output = converter.to_html(parsed)
    print(f"  HTML output length: {len(html_output)} chars")

    print(f"\n  ✓ Format converter tests passed")

    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
