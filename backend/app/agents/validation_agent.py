from __future__ import annotations

import logging

from app.agents.state import AgentState
from app.api.schemas import RiskFinding
from app.services.llm.factory import get_llm_provider
from app.services.risk_registry import RISK_CATEGORIES, get_category_definition

logger = logging.getLogger(__name__)


async def validation_node(state: AgentState) -> AgentState:
    """LangGraph node: validates retrieved chunks against each category using the LLM provider."""
    retrieved_chunks = state.get("retrieved_chunks", [])
    category_keys = state.get("category_keys", [])

    if not retrieved_chunks:
        return {}

    llm = get_llm_provider()
    findings: list[RiskFinding] = []

    for chunk_text, score, page in retrieved_chunks:
        for category_key in category_keys:
            category_name = RISK_CATEGORIES[category_key]["name"]
            category_definition = get_category_definition(category_key)

            try:
                result = await llm.validate_clause(
                    chunk_text,
                    category_name,
                    category_definition,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("ValidationNode: LLM call failed category=%s: %s", category_key, exc)
                continue

            logger.debug(
                "ValidationNode: chunk_score=%.3f category=%s risk=%s snippet=%.80s",
                score,
                category_key,
                result.risk_detected,
                chunk_text,
            )

            if not result.risk_detected:
                continue

            findings.append(
                RiskFinding(
                    category=category_name,
                    page=page,
                    explanation=result.explanation,
                    clause_text=chunk_text,
                )
            )

    logger.info("ValidationNode: produced %d findings", len(findings))
    return {"findings": findings}
