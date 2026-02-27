
from fastapi import APIRouter, HTTPException

from app.api.schemas import AnalyzeRequest, AnalyzeResponse, RiskFinding
from app.services.embedding_service import get_embedding_provider
from app.services.llm.ollama_provider import OllamaLLMProvider
from app.services.risk_registry import RISK_CATEGORIES, get_category_definition
from app.services.vector_store import vector_store


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
    retrieved = vector_store.search(doc_id, query_embedding, top_k=3, min_score=0.25)
    if not retrieved:
        # Retry without min_score to avoid empty results from aggressive filtering
        retrieved = vector_store.search(doc_id, query_embedding, top_k=3, min_score=0.0)
    if not retrieved:
        raise HTTPException(status_code=404, detail="Document not found or no relevant chunks")

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
                continue
            if not result.risk_detected or result.confidence < 0.4:
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
