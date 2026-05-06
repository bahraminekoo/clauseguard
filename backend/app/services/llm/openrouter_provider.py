
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

from app.config import settings
from app.models.risk_models import RiskValidationResult
from app.services.llm.base import LLMProvider
from app.services.llm.types import build_validation_prompt


class OpenRouterLLMProvider(LLMProvider):
    """LLM provider that calls OpenRouter's OpenAI-compatible chat API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or settings.openrouter_api_key
        self.base_url = (base_url or settings.openrouter_base_url).rstrip("/")
        self.model = model or settings.openrouter_llm_model

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is required for OpenRouterLLMProvider")

    async def validate_clause(
        self,
        clause_text: str,
        category_name: str,
        category_definition: str,
    ) -> RiskValidationResult:
        messages = build_validation_prompt(clause_text, category_name, category_definition)

        last_error: Exception | None = None
        for _ in range(2):  # first try + one retry
            try:
                raw_json = await self._chat(messages)
                obj = json.loads(raw_json)
                obj.setdefault("category", "UNKNOWN")
                obj.setdefault("clause_text", clause_text)
                obj.setdefault("page", None)
                parsed = RiskValidationResult.model_validate(obj)
                if not parsed.explanation.strip():
                    parsed.explanation = "Model output invalid: empty explanation"
                return parsed
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue

        return RiskValidationResult(
            risk_detected=False,
            explanation=f"Model output invalid: {last_error}",
            category="UNKNOWN",
            page=None,
            clause_text=clause_text,
        )

    async def _chat(self, messages: list[dict[str, Any]]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        max_retries = 5
        backoff = 2.0
        async with httpx.AsyncClient(timeout=90.0) as client:
            for attempt in range(max_retries):
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                if resp.status_code == 429:
                    wait = backoff * (2 ** attempt)
                    logger.warning("OpenRouter 429 rate limit, retrying in %.1fs (attempt %d/%d)", wait, attempt + 1, max_retries)
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    raise ValueError("No choices in OpenRouter response")
                content = choices[0].get("message", {}).get("content")
                if not isinstance(content, str):
                    raise ValueError("Missing content in OpenRouter response")
                # Validate JSON
                json.loads(content)
                return content
        raise httpx.HTTPStatusError("Rate limited after max retries", request=resp.request, response=resp)
