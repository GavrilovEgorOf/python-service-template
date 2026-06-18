import re

_ROUTE_ID_PATTERN = re.compile(r"/\d+(?=($|/))")


def normalize_metrics_path(path: str) -> str:
    if path == "/metrics":
        return path
    return _ROUTE_ID_PATTERN.sub("/{id}", path)
