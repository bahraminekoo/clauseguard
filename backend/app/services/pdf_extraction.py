
from __future__ import annotations

from io import BytesIO
from PyPDF2 import PdfReader


def extract_text_from_pdf_bytes(data: bytes) -> str:
    """Extract text from pdf bytes and return concatenated page text"""
    reader = PdfReader(BytesIO(data))
    texts: list[str] = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    return "\n".join(texts)
