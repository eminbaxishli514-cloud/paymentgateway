"""Application configuration. Keeps settings in one place for easy adjustment."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore unknown env vars to avoid injection
    )

    app_name: str = "Payment Gateway Demo"
    debug: bool = False
    environment: str = "development"  # development | staging | production

    # Security
    api_key_header: str = "X-API-Key"
    supported_currencies: list[str] = ["USD", "EUR", "GBP"]
    cors_origins: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]
    rate_limit: str = "100/minute"  # Global rate limit
    rate_limit_payment: str = "10/minute"  # Stricter for payment endpoints
    max_request_size: int = 1_000_000  # 1MB max body

    # Admin / SIEM API — send header X-Admin-Token with this value
    admin_api_key: str = "change-me-in-production"

    # SIEM: flag IP if this many requests in 60s (rolling window)
    siem_suspicious_rpm: int = 60
    siem_critical_rpm: int = 200

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
