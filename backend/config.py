"""Central application settings, loaded from environment variables / .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg2://docqa:docqa@localhost:5432/docqa"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    embedding_model_name: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    chunk_size: int = 800
    chunk_overlap: int = 120

    top_k: int = 4


settings = Settings()
