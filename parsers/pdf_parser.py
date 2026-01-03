"""PDF document parser using PyMuPDF."""

import fitz  # PyMuPDF
from pathlib import Path


def parse_pdf(file_path: str | Path) -> str:
    """
    Extract text content from a PDF file.

    Args:
        file_path: Path to the PDF file

    Returns:
        Extracted text content as a string
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    if not file_path.suffix.lower() == '.pdf':
        raise ValueError(f"Not a PDF file: {file_path}")

    text_parts = []

    with fitz.open(file_path) as doc:
        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text()
            if page_text.strip():
                text_parts.append(page_text)

    return "\n\n".join(text_parts)
