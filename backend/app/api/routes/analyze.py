
from fastapi import APIRouter, HTTPException

from app.api.schemas import AnalyzeRequest, AnalyzeResponse, RiskFinding
from app.services.embedding_service import get_embedding_provider
from app.services.llm.ollama_provider import OllamaLLMProvider
from app.services.risk_registry import RISK_CATEGORIES, get_category_definition
from app.services.vector_store import vector_store


router = APIRouter(tags=["analyze"])

DEFAULT_CATEGORY_KEY = "UNLIMITED_LIABILITY"


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    category_keys = payload.category_keys or [DEFAULT_CATEGORY_KEY]
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

    embedder = get_embedding_provider()
    query_embedding = await embedder.embed(query)
    retrieved = vector_store.search(doc_id, query_embedding, top_k=3)
    if not retrieved:
        raise HTTPException(status_code=404, detail="Document not found or no chunks")

    llm = OllamaLLMProvider()
    findings: list[RiskFinding] = []
    for chunk_text, _score in retrieved:
        for category_key, category_definition in resolved_categories:
            try:
                result = await llm.validate_clause(chunk_text, category_definition)
            except Exception as exc:  # noqa: BLE001
                continue
            display_category = RISK_CATEGORIES[category_key]["name"]
            finding = RiskFinding(
                category=display_category,
                confidence=result.confidence,
                page=result.page,
                explanation=result.explanation,
                clause_text=chunk_text,
            )
            findings.append(finding)

    return AnalyzeResponse(findings=findings)
