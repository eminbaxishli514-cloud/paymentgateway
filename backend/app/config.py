"""Application configuration. Keeps settings in one place for easy adjustment."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or defaults."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Payment Gateway Demo"
    debug: bool = False
    api_key_header: str = "X-API-Key"
    supported_currencies: list[str] = ["USD", "EUR", "GBP"]


settings = Settings()
