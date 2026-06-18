#!/usr/bin/env python3
"""Rename the template to a new service name."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OLD = "python-service-template"


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
    args = parser.parse_args()

    new_name = re.sub(r"[^a-z0-9-]", "-", args.new_name.lower()).strip("-")
    if not new_name:
        raise SystemExit("new_name must contain letters or numbers")

    for path in ROOT.rglob("*"):
        if path.is_file() and ".git" not in path.parts and ".venv" not in path.parts:
            replace_in_file(path, args.old_name, new_name)

    print(f"Renamed template from '{args.old_name}' to '{new_name}'")


if __name__ == "__main__":
    main()
