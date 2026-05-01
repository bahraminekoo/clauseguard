
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


class OpenRouterEmbeddingProvider(EmbeddingProvider):
    """Embedding provider that calls OpenRouter's OpenAI-compatible embeddings API."""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def embed(self, text: str) -> List[float]:
        payload = {"model": self.model, "input": text}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/embeddings",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            emb_data = data.get("data")
            if not isinstance(emb_data, list) or not emb_data:
                logger.error(
                    "OpenRouter embedding returned invalid payload: status=%s body=%s",
                    resp.status_code,
                    resp.text[:2000],
                )
                raise ValueError("Invalid embedding response from OpenRouter")
            embedding = emb_data[0].get("embedding")
            if not isinstance(embedding, list) or not embedding:
                raise ValueError("Missing embedding vector in OpenRouter response")
            return embedding

    async def embed_batch(self, texts: Iterable[str]) -> List[List[float]]:
        text_list = list(texts)
        payload = {"model": self.model, "input": text_list}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/embeddings",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            emb_data = data.get("data", [])
            # Sort by index to preserve order
            emb_data.sort(key=lambda x: x.get("index", 0))
            return [item["embedding"] for item in emb_data]


def get_embedding_provider() -> EmbeddingProvider:
    provider = settings.embedding_provider.lower()
    if provider == "openrouter":
        return OpenRouterEmbeddingProvider(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_embedding_model,
        )
    return OllamaEmbeddingProvider(
        base_url=settings.ollama_base_url,
        model=settings.embedding_model,
    )
