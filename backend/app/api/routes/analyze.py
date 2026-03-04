
import logging

from fastapi import APIRouter, HTTPException

from app.agents.orchestrator import run_pipeline
from app.api.schemas import AnalyzeRequest, AnalyzeResponse, RiskFinding
from app.services.llm.ollama_provider import OllamaLLMProvider
from app.services.risk_registry import RISK_CATEGORIES, get_category_definition

logger = logging.getLogger(__name__)


router = APIRouter(tags=["analyze"])

# Default to all known categories when none are provided so we don't bias to a single class
DEFAULT_CATEGORY_KEYS = list(RISK_CATEGORIES.keys())


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    category_keys = payload.category_keys or DEFAULT_CATEGORY_KEYS

    # Validate category keys early
    for ck in category_keys:
        if ck not in RISK_CATEGORIES:
            raise HTTPException(status_code=400, detail=f"Unknown category: {ck}")

    # Handle backward compatibility with old text-only requests
    if payload.text and not payload.doc_id:
        text = payload.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="text is required")

        llm = OllamaLLMProvider()
        findings: list[RiskFinding] = []
        for ck in category_keys:
            category_definition = get_category_definition(ck)
            try:
                result = await llm.validate_clause(text, RISK_CATEGORIES[ck]["name"], category_definition)
            except Exception as exc:  # noqa: BLE001
                continue

            findings.append(
                RiskFinding(
                    category=RISK_CATEGORIES[ck]["name"],
                    confidence=result.confidence,
                    page=result.page,
                    explanation=result.explanation,
                    clause_text=text,
                )
            )

        return AnalyzeResponse(findings=findings)

    # Agent-based pipeline: doc_id + query_text
    if not payload.doc_id or not payload.query_text:
        raise HTTPException(status_code=400, detail="Either 'text' OR both 'doc_id' and 'query_text' are required")

    response, error = await run_pipeline(
        doc_id=payload.doc_id,
        query_text=payload.query_text,
        category_keys=category_keys,
    )

    if error:
        raise HTTPException(status_code=404, detail=error)

    return response
