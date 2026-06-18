from app.core.metrics_paths import normalize_metrics_path


def test_normalize_metrics_path_replaces_numeric_ids() -> None:
    assert normalize_metrics_path("/api/v1/items/42") == "/api/v1/items/{id}"


def test_metrics_path_unchanged_for_health() -> None:
    assert normalize_metrics_path("/health/live") == "/health/live"
