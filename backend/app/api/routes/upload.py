import logging

from fastapi import APIRouter, File, HTTPException, UploadFile
from app.api.schemas import UploadResponse
from app.services.chunking import chunk_with_pages
from app.services.embedding_service import get_embedding_provider
from app.services.pdf_extraction import extract_text_from_pdf_bytes
from app.services.vector_store import vector_store


logger = logging.getLogger(__name__)


router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    data = await file.read()
    try:
        pages = extract_text_from_pdf_bytes(data)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Upload failed: extractor error: %s", exc)
        raise HTTPException(status_code=400, detail="Failed to read PDF") from exc

    logger.warning("Extracted %s pages", len(pages))
    if not pages:
        raise HTTPException(status_code=400, detail="No pages could be read from PDF")

    try:
        chunks, page_numbers = chunk_with_pages(pages)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Chunking failed: %s", exc)
        raise HTTPException(status_code=400, detail="Failed to chunk PDF text") from exc

    logger.warning("Chunked into %s chunks", len(chunks))
    if not chunks:
        raise HTTPException(status_code=400, detail=f"No text extracted from PDF (pages={len(pages)})")

    embedder = get_embedding_provider()
    embeddings = await embedder.embed_batch(chunks)
    doc_id = vector_store.add_document(chunks, embeddings, pages=page_numbers)
    logger.info("Stored doc_id=%s with %s chunks", doc_id, len(chunks))
    return UploadResponse(doc_id=doc_id)
