from __future__ import annotations

import logging
from typing import List

from langgraph.graph import END, StateGraph

from app.agents.document_agent import document_node
from app.agents.retrieval_agent import retrieval_node
from app.agents.state import AgentState
from app.agents.validation_agent import validation_node
from app.api.schemas import AnalyzeResponse
from app.services.risk_registry import RISK_CATEGORIES

logger = logging.getLogger(__name__)

DEFAULT_CATEGORY_KEYS = list(RISK_CATEGORIES.keys())


def _has_error(state: AgentState) -> str:
    """Conditional edge: route to END if an error was set, otherwise continue."""
    if state.get("error"):
        return "end"
    return "continue"


def build_graph() -> StateGraph:
    """Build and compile the LangGraph agent pipeline."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("document", document_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("validation", validation_node)

    # Set entry point
    graph.set_entry_point("document")

    # Conditional edges: stop on error, otherwise proceed to next node
    graph.add_conditional_edges("document", _has_error, {"end": END, "continue": "retrieval"})
    graph.add_conditional_edges("retrieval", _has_error, {"end": END, "continue": "validation"})
    graph.add_edge("validation", END)

    return graph.compile()


# Compiled graph singleton
_compiled_graph = build_graph()


async def run_pipeline(
    doc_id: str,
    query_text: str,
    category_keys: List[str] | None = None,
) -> tuple[AnalyzeResponse | None, str | None]:
    """
    Execute the LangGraph agent pipeline.

    Returns:
        (AnalyzeResponse, None) on success
        (None, error_message) on failure
    """
    initial_state: AgentState = {
        "doc_id": doc_id,
        "query_text": query_text,
        "category_keys": category_keys or DEFAULT_CATEGORY_KEYS,
    }

    logger.info("Orchestrator: invoking pipeline for doc_id=%s", doc_id)
    result = await _compiled_graph.ainvoke(initial_state)

    error = result.get("error")
    if error:
        logger.warning("Orchestrator: pipeline error: %s", error)
        return None, error

    findings = result.get("findings", [])
    logger.info("Orchestrator: pipeline completed with %d findings", len(findings))
    return AnalyzeResponse(findings=findings), None
