
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List

import httpx

from app.config import settings


class EmbeddingProvider(ABC):
    """Provider-agnostic embedding interface."""

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Return embedding vector for a single string."""
        raise NotImplementedError

    async def embed_batch(self, texts: Iterable[str]) -> List[List[float]]:
        """Default batch implementation; providers may override for efficiency."""
        return [await self.embed(t) for t in texts]


class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def embed(self, text: str) -> List[float]:
        payload = {"model": self.model, "input": text}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.base_url}/api/embeddings", json=payload)
            resp.raise_for_status()
            data = resp.json()
            embedding = data.get("embedding")
            if not isinstance(embedding, list):
                raise ValueError("Invalid embedding response from provider")
            return embedding


def get_embedding_provider() -> EmbeddingProvider:
    return OllamaEmbeddingProvider(
        base_url=settings.ollama_base_url,
        model=settings.embedding_model,
    )
