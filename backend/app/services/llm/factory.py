
from app.config import settings
from app.services.llm.base import LLMProvider


def get_llm_provider() -> LLMProvider:
    provider = settings.llm_provider.lower()
    if provider == "openrouter":
        from app.services.llm.openrouter_provider import OpenRouterLLMProvider
        return OpenRouterLLMProvider()
    from app.services.llm.ollama_provider import OllamaLLMProvider
    return OllamaLLMProvider()
