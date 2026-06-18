import pytest
from app.core.config import Settings


def test_production_settings_rejects_insecure_defaults() -> None:
    with pytest.raises(ValueError, match="AUTH_DISABLED"):
        Settings(
            environment="production",
            auth_disabled=True,
            api_key="prod-api-key",
            jwt_secret_key="prod-jwt-secret",
        )


def test_production_settings_requires_secrets() -> None:
    with pytest.raises(ValueError, match="API_KEY"):
        Settings(
            environment="production",
            auth_disabled=False,
            api_key="dev-api-key-change-me",
            jwt_secret_key="prod-jwt-secret",
        )
