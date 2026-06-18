from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DEV_API_KEY = "dev-api-key-change-me"
DEFAULT_DEV_JWT_SECRET = "dev-jwt-secret-change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "python-service-template"
    app_version: str = "0.5.0"
    environment: str = "development"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    redis_url: str | None = "redis://localhost:6379/0"

    api_v1_prefix: str = "/api/v1"
    auth_disabled: bool = False
    api_key: str | None = None

    jwt_secret_key: str | None = None
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "python-service-template"
    jwt_audience: str = "python-service-template-api"

    otel_enabled: bool = False
    otel_exporter_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "python-service-template"
    otel_insecure: bool = True

    metrics_enabled: bool = True
    metrics_api_key: str | None = None

    cache_ttl_seconds: int = 60
    idempotency_ttl_seconds: int = 86400
    idempotency_lock_ttl_seconds: int = 60

    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    audit_log_enabled: bool = True
    audit_log_persist: bool = False

    cors_origins: str = ""

    log_level: str = "INFO"
    log_json: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: object) -> str:
        if isinstance(value, list):
            return ",".join(str(item) for item in value)
        return str(value) if value is not None else ""

    @property
    def cors_origin_list(self) -> list[str]:
        if not self.cors_origins.strip():
            return ["http://localhost:3000", "http://127.0.0.1:3000"] if self.debug else []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @property
    def effective_metrics_api_key(self) -> str | None:
        return self.metrics_api_key or self.api_key

    @model_validator(mode="after")
    def validate_production_rules(self) -> "Settings":
        if not self.is_production:
            return self

        errors: list[str] = []
        if self.auth_disabled:
            errors.append("AUTH_DISABLED must be false in production")
        if not self.api_key or self.api_key == DEFAULT_DEV_API_KEY:
            errors.append("API_KEY must be set to a non-default secret in production")
        if not self.jwt_secret_key or self.jwt_secret_key == DEFAULT_DEV_JWT_SECRET:
            errors.append("JWT_SECRET_KEY must be set to a non-default secret in production")
        if self.debug:
            errors.append("DEBUG must be false in production")
        if self.otel_insecure and self.otel_enabled:
            errors.append("OTEL_INSECURE should be false when OTEL is enabled in production")

        if errors:
            raise ValueError("; ".join(errors))
        return self


settings = Settings()
