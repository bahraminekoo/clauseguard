
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "ClauseGuard API"
    environment: str = "local"
    # Comma-separated origins for CORS
    cors_allow_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Provider selection: "ollama" or "openrouter"
    llm_provider: str = "ollama"
    embedding_provider: str = "ollama"

    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3"
    embedding_model: str = "bge-large"

    # OpenRouter settings
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_llm_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    openrouter_embedding_model: str = "nvidia/llama-nemotron-embed-vl-1b-v2:free"


settings = Settings()
