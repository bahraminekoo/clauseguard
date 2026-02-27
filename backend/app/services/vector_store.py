
from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Tuple
import numpy as np


@dataclass
class StoredChunk:
    text: str
    embedding: List[float]
    page: int | None = None


class InMemoryVectorStore:
    def __init__(self, storage_path: Path | None = None) -> None:
        self._store: dict[str, list[StoredChunk]] = {}
        self._storage_path = storage_path
        if self._storage_path:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._load()

    def add_document(self, chunks: List[str], embeddings: List[List[float]], pages: List[int] | None = None) -> str:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings length mismatch")
        if pages and len(pages) != len(chunks):
            raise ValueError("pages length mismatch")
        doc_id = str(uuid.uuid4())
        stored = []
        for c, e, p in zip(chunks, embeddings, pages or [None] * len(chunks)):
            stored.append(StoredChunk(text=c, embedding=e, page=p))
        self._store[doc_id] = stored
        self._save()
        return doc_id

    def search(self, doc_id: str, query_embedding: List[float], top_k: int = 3, min_score: float = 0.0) -> List[Tuple[str, float, int | None]]:
        items = self._store.get(doc_id)
        if not items:
            return []

        q = np.array(query_embedding, dtype=float)
        scores: list[tuple[str, float, int | None]] = []
        for chunk in items:
            v = np.array(chunk.embedding, dtype=float)
            denom = (np.linalg.norm(q) * np.linalg.norm(v)) or 1e-8
            score = float(np.dot(q, v) / denom)
            if score >= min_score:
                scores.append((chunk.text, score, chunk.page))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def _save(self) -> None:
        if not self._storage_path:
            return
        serializable: dict[str, list[dict]] = {}
        for doc_id, chunks in self._store.items():
            serializable[doc_id] = [asdict(c) for c in chunks]
        self._storage_path.write_text(json.dumps(serializable))

    def _load(self) -> None:
        if not self._storage_path or not self._storage_path.exists():
            return
        try:
            raw = json.loads(self._storage_path.read_text())
            for doc_id, chunks in raw.items():
                self._store[doc_id] = [StoredChunk(**c) for c in chunks]
        except Exception:
            # if corrupt, reset
            self._store = {}


# Singleton store for simplicity (persisted to disk)
_default_storage = Path(__file__).resolve().parent.parent / "storage" / "vector_store.json"
vector_store = InMemoryVectorStore(storage_path=_default_storage)
