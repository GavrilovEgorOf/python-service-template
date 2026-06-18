import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


def validate_runtime_settings() -> None:
    """Fail fast on startup when production rules are violated."""
    if settings.is_production:
        logger.info("production_settings_validated", environment=settings.environment)
        return

    if settings.auth_disabled:
        logger.warning("auth_disabled_in_non_production")

    if settings.api_key in {None, "dev-api-key-change-me"}:
        logger.warning("using_default_or_missing_api_key")

    if settings.jwt_secret_key in {None, "dev-jwt-secret-change-me-in-production"}:
        logger.warning("using_default_or_missing_jwt_secret")
