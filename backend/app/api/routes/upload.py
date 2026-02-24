from fastapi import APIRouter, File, HTTPException, UploadFile
from app.api.schemas import UploadResponse
from app.services.chunking import chunk_text
from app.services.embedding_service import get_embedding_provider
from app.services.pdf_extraction import extract_text_from_pdf_bytes
from app.services.vector_store import vector_store


router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    data = await file.read()
    text = extract_text_from_pdf_bytes(data)
    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="No text extracted from PDF")

    embedder = get_embedding_provider()
    embeddings = await embedder.embed_batch(chunks)
    doc_id = vector_store.add_document(chunks, embeddings)
    return UploadResponse(doc_id=doc_id)
