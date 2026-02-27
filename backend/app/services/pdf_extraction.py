
from __future__ import annotations

import logging
from io import BytesIO
from pdfminer.high_level import extract_text
from pdfminer.pdfpage import PDFPage
from PyPDF2 import PdfReader
import pypdfium2 as pdfium
import pytesseract
from PIL import Image


logger = logging.getLogger(__name__)


def extract_text_from_pdf_bytes(data: bytes) -> list[tuple[int, str]]:
    """Extract text from pdf bytes and return list of (page_number, text) using pdfminer."""
    pages: list[tuple[int, str]] = []

    try:
        for page_num, _ in enumerate(PDFPage.get_pages(BytesIO(data)), start=1):
            try:
                text = extract_text(BytesIO(data), page_numbers=[page_num - 1]) or ""
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping unreadable page %s: %s", page_num, exc)
                continue
            pages.append((page_num, text.strip()))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to process PDF: %s", exc)
        raise

    # Fallback to PyPDF2 if no text was extracted
    if not pages or all(not txt for _, txt in pages):
        logger.info("pdfminer extracted no text; falling back to PyPDF2")
        reader = PdfReader(BytesIO(data))
        pages = []
        for idx, page in enumerate(reader.pages, start=1):
            try:
                txt = page.extract_text() or ""
            except Exception as exc:  # noqa: BLE001
                logger.warning("PyPDF2 skipping unreadable page %s: %s", idx, exc)
                continue
            pages.append((idx, txt.strip()))

    # Fallback to OCR if still empty or all blank
    if not pages or all(not txt for _, txt in pages):
        logger.info("No text after parsers; falling back to OCR")
        pages = []
        try:
            pdf = pdfium.PdfDocument(data)
            for page_index in range(len(pdf)):
                page = pdf.get_page(page_index)
                bitmap = page.render(scale=2.0, rotation=0)
                pil_image = bitmap.to_pil()
                ocr_text = pytesseract.image_to_string(pil_image) or ""
                pages.append((page_index + 1, ocr_text.strip()))
        except Exception as exc:  # noqa: BLE001
            logger.warning("OCR fallback failed: %s", exc)
            # keep whatever pages we have (likely empty)

    return pages
