
import json
import pytest
import respx
from httpx import Response

from app.services.llm.ollama_provider import OllamaLLMProvider


@pytest.mark.asyncio
async def test_validate_clause_parses_valid_json():
    provider = OllamaLLMProvider(base_url="http://ollama")

    with respx.mock(base_url="http://ollama") as mock:
        mock.post("/api/chat").mock(
            return_value=Response(
                200,
                json={
                    "message": {"content": json.dumps({
                        "risk_detected": True,
                        "confidence": 0.82,
                        "explanation": "Unlimited liability detected.",
                    })}
                },
            )
        )

        result = await provider.validate_clause("clause text", "definition")

    assert result.risk_detected is True
    assert result.confidence == 0.82
    assert result.explanation.startswith("Unlimited liability")
    assert result.category == "UNKNOWN"  # category is filled upstream
    assert result.clause_text == "clause text"


@pytest.mark.asyncio
async def test_validate_clause_retries_and_returns_safe_failure():
    provider = OllamaLLMProvider(base_url="http://ollama")

    with respx.mock(base_url="http://ollama") as mock:
        # First response: invalid JSON string
        mock.post("/api/chat").mock(
            side_effect=[
                Response(200, json={"message": {"content": "not-json"}}),
                Response(200, json={"message": {"content": "still-bad"}}),
            ]
        )

        result = await provider.validate_clause("clause text", "definition")

    assert result.risk_detected is False
    assert result.confidence == 0.0
    assert "invalid" in result.explanation.lower()
    assert result.category == "UNKNOWN"
    assert result.clause_text == "clause text"
