from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    # AI Providers (for BYOK)
    GEMINI_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    COHERE_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None
    OLLAMA_HOST: str = "http://localhost:11434"

    # Security
    APP_SECRET_KEY: str = "default-secret-key-please-change"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()
