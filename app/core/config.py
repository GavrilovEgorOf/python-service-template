from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "python-service-template"
    app_version: str = "0.4.0"
    environment: str = "development"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    redis_url: str | None = "redis://localhost:6379/0"

    api_v1_prefix: str = "/api/v1"
    auth_disabled: bool = False
    api_key: str | None = "dev-api-key-change-me"

    otel_enabled: bool = False
    otel_exporter_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "python-service-template"

    metrics_enabled: bool = True
    cache_ttl_seconds: int = 60
    idempotency_ttl_seconds: int = 86400

    log_level: str = "INFO"
    log_json: bool = False


settings = Settings()
