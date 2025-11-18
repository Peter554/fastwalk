"""Shared test fixtures and utilities."""

from pathlib import Path

import powerwalk


def create_file(path, content=""):
    """Helper to create a file, creating parent directories if needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def by_path(
    entries: list[powerwalk.DirEntry],
) -> dict[Path, powerwalk.DirEntry]:
    return {e.path: e for e in entries}
