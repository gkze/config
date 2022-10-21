#!/usr/bin/env python3
# vi: ft=python
from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).parent
IGNORE: set[str] = {".git", ".mypy_cache", "__pycache__"}


def walk(path: Path):
    for p in Path(path).iterdir():
        if set(p.parts) & IGNORE:
            continue

        if p.is_dir():
            yield from walk(p)
            continue

        yield p
