
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List

import httpx
import logging

from app.config import settings


class EmbeddingProvider(ABC):
    """Provider-agnostic embedding interface."""

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Return embedding vector for a single string."""
        raise NotImplementedError

    async def embed_batch(self, texts: Iterable[str]) -> List[List[float]]:
        """Default batch implementation, providers may override for efficiency."""
        vectors = [await self.embed(t) for t in texts]
        return vectors


logger = logging.getLogger(__name__)


class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def embed(self, text: str) -> List[float]:
        # Ollama embeddings endpoint expects the text under the "prompt" key
        payload = {"model": self.model, "prompt": text}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.base_url}/api/embeddings", json=payload)
            resp.raise_for_status()
            data = resp.json()
            embedding = data.get("embedding")
            if not isinstance(embedding, list) or not embedding:
                logger.error(
                    "Embedding provider returned invalid payload: status=%s model=%s url=%s body=%s",
                    resp.status_code,
                    self.model,
                    resp.url,
                    resp.text[:2000],
                )
                raise ValueError("Invalid embedding response from provider (empty or missing)")
            return embedding


def get_embedding_provider() -> EmbeddingProvider:
    return OllamaEmbeddingProvider(
        base_url=settings.ollama_base_url,
        model=settings.embedding_model,
    )
