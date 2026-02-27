
import logging

from fastapi import APIRouter, HTTPException

from app.api.schemas import AnalyzeRequest, AnalyzeResponse, RiskFinding
from app.services.embedding_service import get_embedding_provider
from app.services.llm.ollama_provider import OllamaLLMProvider
from app.services.risk_registry import RISK_CATEGORIES, get_category_definition, get_category_seed_query
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)


router = APIRouter(tags=["analyze"])

# Default to all known categories when none are provided so we don't bias to a single class
DEFAULT_CATEGORY_KEYS = list(RISK_CATEGORIES.keys())


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    category_keys = payload.category_keys or DEFAULT_CATEGORY_KEYS
    resolved_categories: list[tuple[str, str]] = []
    try:
        for ck in category_keys:
            definition = get_category_definition(ck)
            resolved_categories.append((ck, definition))
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown category: {exc}") from exc

    # Handle backward compatibility with old text-only requests
    if payload.text and not payload.doc_id:
        text = payload.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="text is required")

        llm = OllamaLLMProvider()
        findings: list[RiskFinding] = []
        for category_key, category_definition in resolved_categories:
            try:
                result = await llm.validate_clause(text, category_definition)
            except Exception as exc:  # noqa: BLE001
                continue

            display_category = RISK_CATEGORIES[category_key]["name"]
            finding = RiskFinding(
                category=display_category,
                confidence=result.confidence,
                page=result.page,
                explanation=result.explanation,
                clause_text=text,
            )
            findings.append(finding)

        return AnalyzeResponse(findings=findings)

    # New behavior: doc_id + query_text with retrieval
    if not payload.doc_id or not payload.query_text:
        raise HTTPException(status_code=400, detail="Either 'text' OR both 'doc_id' and 'query_text' are required")

    doc_id = payload.doc_id.strip()
    query = payload.query_text.strip()

    # Ensure document exists before embedding work
    if doc_id not in vector_store._store:  # type: ignore[attr-defined]
        raise HTTPException(status_code=404, detail="Document not found. Please upload again and use the returned doc_id.")

    embedder = get_embedding_provider()
    query_embedding = await embedder.embed(query)

    # Gather chunks via user query
    retrieved_map: dict[str, tuple[str, float, int | None]] = {}
    user_results = vector_store.search(doc_id, query_embedding, top_k=10, min_score=0.15)
    if not user_results:
        user_results = vector_store.search(doc_id, query_embedding, top_k=10, min_score=0.0)
    for chunk_text, score, page in user_results:
        if chunk_text not in retrieved_map or score > retrieved_map[chunk_text][1]:
            retrieved_map[chunk_text] = (chunk_text, score, page)

    # Augment with category seed queries
    for category_key, _ in resolved_categories:
        seed_query = get_category_seed_query(category_key)
        if not seed_query:
            continue
        seed_embedding = await embedder.embed(seed_query)
        seed_results = vector_store.search(doc_id, seed_embedding, top_k=10, min_score=0.15)
        if not seed_results:
            seed_results = vector_store.search(doc_id, seed_embedding, top_k=5, min_score=0.0)
        for chunk_text, score, page in seed_results:
            if chunk_text not in retrieved_map or score > retrieved_map[chunk_text][1]:
                retrieved_map[chunk_text] = (chunk_text, score, page)

    retrieved = list(retrieved_map.values())
    if not retrieved:
        raise HTTPException(status_code=404, detail="Document not found or no relevant chunks")

    logger.info("doc_id=%s retrieved %d unique chunks for validation", doc_id, len(retrieved))

    llm = OllamaLLMProvider()
    findings: list[RiskFinding] = []
    for chunk_text, score, page in retrieved:
        for category_key, category_definition in resolved_categories:
            try:
                result = await llm.validate_clause(
                    chunk_text,
                    RISK_CATEGORIES[category_key]["name"],
                    category_definition,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("LLM call failed for category=%s: %s", category_key, exc)
                continue
            logger.debug(
                "chunk_score=%.3f category=%s risk=%s confidence=%.2f snippet=%.80s",
                score,
                category_key,
                result.risk_detected,
                result.confidence,
                chunk_text,
            )
            if not result.risk_detected or result.confidence < 0.3:
                continue
            display_category = RISK_CATEGORIES[category_key]["name"]
            finding = RiskFinding(
                category=display_category,
                confidence=result.confidence,
                page=page,
                explanation=result.explanation,
                clause_text=chunk_text,
            )
            findings.append(finding)

    return AnalyzeResponse(findings=findings)
