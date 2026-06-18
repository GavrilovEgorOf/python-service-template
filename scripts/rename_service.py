#!/usr/bin/env python3
"""Rename the template to a new service name."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OLD = "python-service-template"
SKIP_DIRS = {".git", ".venv", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__"}
TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".toml",
    ".ini",
    ".yml",
    ".yaml",
    ".env",
    ".example",
    ".json",
    ".txt",
}


def replace_in_file(path: Path, old: str, new: str) -> None:
    content = path.read_text(encoding="utf-8")
    updated = content.replace(old, new)
    updated = updated.replace(old.replace("-", "_"), new.replace("-", "_"))
    if updated != content:
        path.write_text(updated, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rename python-service-template")
    parser.add_argument("new_name", help="New service name, e.g. billing-api")
    parser.add_argument("--old-name", default=DEFAULT_OLD)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    new_name = re.sub(r"[^a-z0-9-]", "-", args.new_name.lower()).strip("-")
    if not new_name:
        raise SystemExit("new_name must contain letters or numbers")

    changed: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if SKIP_DIRS.intersection(path.parts):
            continue
        if path.suffix and path.suffix not in TEXT_EXTENSIONS and path.name != ".env.example":
            continue
        content = path.read_text(encoding="utf-8")
        candidate = content.replace(args.old_name, new_name)
        candidate = candidate.replace(args.old_name.replace("-", "_"), new_name.replace("-", "_"))
        if candidate != content:
            changed.append(path)
            if not args.dry_run:
                replace_in_file(path, args.old_name, new_name)

    action = "Would rename" if args.dry_run else "Renamed"
    print(f"{action} template from '{args.old_name}' to '{new_name}' ({len(changed)} files)")
    for path in changed:
        print(f"  - {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
