
from fastapi import APIRouter, HTTPException

from app.api.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.llm.ollama_provider import OllamaLLMProvider
from app.services.risk_registry import RISK_CATEGORIES, get_category_definition


router = APIRouter(tags=["analyze"])

DEFAULT_CATEGORY_KEY = "UNLIMITED_LIABILITY"


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    category_key = DEFAULT_CATEGORY_KEY
    try:
        category_definition = get_category_definition(category_key)
    except KeyError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    llm = OllamaLLMProvider()
    try:
        result = await llm.validate_clause(text, category_definition)
    except Exception as exc:  # noqa: BLE001 - we surface structured error
        raise HTTPException(status_code=502, detail=f"LLM validation failed: {exc}") from exc

    display_category = RISK_CATEGORIES[category_key]["name"]
    finding = result.model_copy(update={"category": display_category})
    return AnalyzeResponse(findings=[finding])
