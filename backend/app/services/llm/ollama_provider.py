
from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import settings
from app.models.risk_models import RiskValidationResult
from app.services.llm.base import LLMProvider
from app.services.llm.types import build_validation_prompt


class OllamaLLMProvider(LLMProvider):
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.llm_model

    async def validate_clause(
        self,
        clause_text: str,
        category_definition: str,
    ) -> RiskValidationResult:
        messages = build_validation_prompt(clause_text, category_definition)

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
            except Exception as exc:  # noqa: BLE001 - want to catch validation/JSON
                last_error = exc
                continue

        # On failure, return a safe negative result (no raw text leakage)
        return RiskValidationResult(
            risk_detected=False,
            confidence=0.0,
            explanation=f"Model output invalid: {last_error}",
            category="UNKNOWN",
            page=None,
            clause_text=clause_text,
        )

    async def _chat(self, messages: list[dict[str, Any]]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json",  # ask Ollama to enforce JSON
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = (data.get("message") or {}).get("content")
            if not isinstance(content, str):
                raise ValueError("Missing content in provider response")
            # Ensure string is valid JSON
            json.loads(content)
            return content
