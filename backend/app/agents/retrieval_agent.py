from __future__ import annotations

import logging

from app.agents.state import AgentState
from app.services.embedding_service import get_embedding_provider
from app.services.risk_registry import get_category_seed_query
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)

TOP_K = 10
MIN_SCORE = 0.15
FALLBACK_MIN_SCORE = 0.0


async def retrieval_node(state: AgentState) -> AgentState:
    """LangGraph node: embeds user query and category seed queries, retrieves relevant chunks."""
    doc_id = state.get("doc_id", "").strip()
    query = state.get("query_text", "").strip()
    category_keys = state.get("category_keys", [])

    if not query:
        return {"error": "query_text is required"}

    embedder = get_embedding_provider()

    # De-duplicate by chunk text, keeping highest score
    retrieved_map: dict[str, tuple[str, float, int | None]] = {}

    # 1) User query retrieval
    query_embedding = await embedder.embed(query)
    user_results = vector_store.search(doc_id, query_embedding, top_k=TOP_K, min_score=MIN_SCORE)
    if not user_results:
        user_results = vector_store.search(doc_id, query_embedding, top_k=TOP_K, min_score=FALLBACK_MIN_SCORE)
    for chunk_text, score, page in user_results:
        if chunk_text not in retrieved_map or score > retrieved_map[chunk_text][1]:
            retrieved_map[chunk_text] = (chunk_text, score, page)

    # 2) Category seed query retrieval
    for category_key in category_keys:
        seed_query = get_category_seed_query(category_key)
        if not seed_query:
            continue
        seed_embedding = await embedder.embed(seed_query)
        seed_results = vector_store.search(doc_id, seed_embedding, top_k=TOP_K, min_score=MIN_SCORE)
        if not seed_results:
            seed_results = vector_store.search(doc_id, seed_embedding, top_k=5, min_score=FALLBACK_MIN_SCORE)
        for chunk_text, score, page in seed_results:
            if chunk_text not in retrieved_map or score > retrieved_map[chunk_text][1]:
                retrieved_map[chunk_text] = (chunk_text, score, page)

    chunks = list(retrieved_map.values())
    logger.info(
        "RetrievalNode: doc_id=%s retrieved %d unique chunks (user_query + %d seed queries)",
        doc_id,
        len(chunks),
        len(category_keys),
    )

    if not chunks:
        return {"error": "No relevant chunks found in the document"}

    return {"retrieved_chunks": chunks}
