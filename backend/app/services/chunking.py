
from __future__ import annotations
from typing import Iterable, List, Tuple

def chunk_text(text: str, max_chars: int = 800, overlap: int = 100) -> List[str]:
    """Chunk text into overlapping segments for retrieval"""
    cleaned = text.replace("\r", " ").strip()
    if not cleaned:
        return []

    chunks: list[str] = []
    start = 0
    n = len(cleaned)
    while start < n:
        end = min(start + max_chars, n)
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks


def chunk_iterable(texts: Iterable[str], max_chars: int = 800, overlap: int = 100) -> List[str]:
    all_chunks: list[str] = []
    for t in texts:
        all_chunks.extend(chunk_text(t, max_chars=max_chars, overlap=overlap))
    return all_chunks


def chunk_with_pages(pages: list[tuple[int, str]], max_chars: int = 800, overlap: int = 100) -> Tuple[List[str], List[int]]:
    """Chunk per-page text and keep page numbers aligned with chunks."""
    chunks: list[str] = []
    page_numbers: list[int] = []
    for page_num, text in pages:
        page_chunks = chunk_text(text, max_chars=max_chars, overlap=overlap)
        chunks.extend(page_chunks)
        page_numbers.extend([page_num] * len(page_chunks))
    return chunks, page_numbers
