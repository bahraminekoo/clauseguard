from __future__ import annotations

from typing import List, Tuple, TypedDict

from app.api.schemas import RiskFinding


class AgentState(TypedDict, total=False):
    """LangGraph-compatible state passed between nodes in the pipeline."""

    # --- Inputs (set before graph invocation) ---
    doc_id: str
    query_text: str
    category_keys: List[str]

    # --- Intermediate (populated by retrieval node) ---
    # Each tuple: (chunk_text, similarity_score, page_number_or_None)
    retrieved_chunks: List[Tuple[str, float, int | None]]

    # --- Outputs (populated by validation node) ---
    findings: List[RiskFinding]

    # --- Error (set by any node to halt the pipeline) ---
    error: str
