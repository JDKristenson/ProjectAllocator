"""Plain text and markdown parser."""

from pathlib import Path


def parse_text(file_path: str | Path) -> str:
    """
    Read text content from a plain text or markdown file.

    Args:
        file_path: Path to the text file

    Returns:
        File content as a string
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Text file not found: {file_path}")

    # Try common encodings
    encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']

    for encoding in encodings:
        try:
            return file_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

    # Fallback: read with error handling
    return file_path.read_text(encoding='utf-8', errors='replace')
