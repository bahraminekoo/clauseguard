from __future__ import annotations

import logging

from app.agents.state import AgentState
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)


async def document_node(state: AgentState) -> AgentState:
    """LangGraph node: validates that the requested document exists in the vector store."""
    doc_id = state.get("doc_id", "").strip()
    if not doc_id:
        return {"error": "doc_id is required"}

    if doc_id not in vector_store._store:  # type: ignore[attr-defined]
        return {"error": "Document not found. Please upload again and use the returned doc_id."}

    logger.info("DocumentNode: doc_id=%s verified (%d chunks stored)", doc_id, len(vector_store._store[doc_id]))
    return {}
