#!/usr/bin/env python3
# vi: ft=python
from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).parent


def walk(path: Path):
    for p in Path(path).iterdir():
        if p.is_dir():
            yield from walk(p)
            continue
        yield p.resolve()
