
from __future__ import annotations
import uuid
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np


@dataclass
class StoredChunk:
    text: str
    embedding: List[float]


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._store: dict[str, list[StoredChunk]] = {}

    def add_document(self, chunks: List[str], embeddings: List[List[float]]) -> str:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings length mismatch")
        doc_id = str(uuid.uuid4())
        self._store[doc_id] = [StoredChunk(text=c, embedding=e) for c, e in zip(chunks, embeddings)]
        return doc_id

    def search(self, doc_id: str, query_embedding: List[float], top_k: int = 3) -> List[Tuple[str, float]]:
        items = self._store.get(doc_id)
        if not items:
            return []

        q = np.array(query_embedding, dtype=float)
        scores: list[tuple[str, float]] = []
        for chunk in items:
            v = np.array(chunk.embedding, dtype=float)
            denom = (np.linalg.norm(q) * np.linalg.norm(v)) or 1e-8
            score = float(np.dot(q, v) / denom)
            scores.append((chunk.text, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# Singleton store for simplicity
vector_store = InMemoryVectorStore()
