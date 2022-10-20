#!/usr/bin/env python3
# vi: ft=python
from __future__ import annotations

import multiprocessing
import sys
from concurrent.futures import Future, ThreadPoolExecutor
from enum import Enum, unique
from pathlib import Path
from typing import Any

from common import PROJECT_ROOT, walk

DEFAULT_DIR_MODE: int = 0o700
SYMLINK_ROOT: Path = Path.home()


@unique
class Action(Enum):
    DO = "do"
    UNDO = "undo"


def src_pretty(src: Path) -> str:
    return str(src).replace(str(SYMLINK_ROOT), "~")


def dest_pretty(dest: Path) -> str:
    return str(dest.relative_to(PROJECT_ROOT))


def link(src: Path, dest: Path) -> None:
    srcp: str = src_pretty(src)
    destp: str = dest_pretty(dest)

    if not dest.is_file():
        print(f"{destp} is not a file - skipping")
        return

    if src.is_symlink():
        if src.readlink() == dest:
            print(f"{srcp} already symlinks to {destp} - skipping")
            return

        else:
            print(f"{srcp} symlink already exists but not to {destp} - unlinking")
            src.unlink()

    if src.exists() and not src.is_symlink():
        print(f"{srcp} is not a symlink - skipping")
        return

    if dest.is_file() and not src.parent.exists():
        print(
            str(src.parent.relative_to(SYMLINK_ROOT)).replace(str(SYMLINK_ROOT), "~")
            + "does not exist - creating"
        )
        src.parent.mkdir(DEFAULT_DIR_MODE, True)

    print(f"linking {srcp} to {destp}")
    src.symlink_to(dest)


def unlink(src: Path, dest: Path) -> None:
    srcp: str = src_pretty(src)
    destp: str = dest_pretty(dest)

    if src.exists():
        if not src.is_symlink():
            print(f"{srcp} is not a symlink - skipping")
            return

        print(f"unlinking {srcp} from {destp}")
        src.unlink()


def main(action: Action) -> None:
    futures: set[Future] = set()
    home_tree: Path = PROJECT_ROOT / "home"

    with ThreadPoolExecutor(multiprocessing.cpu_count()) as tpe:
        for src in walk(home_tree):
            minpath: Path = Path(*src.relative_to(PROJECT_ROOT).parts[1:])

            # fmt: off
            futures.add(tpe.submit(
                link if action == Action.DO else unlink,
                SYMLINK_ROOT / minpath, home_tree / minpath,
            ))
            # fmt: on

    for future in futures:
        result: Any = future.result()
        if result is not None:
            print(result)


if __name__ == "__main__":
    main(Action(sys.argv[1]) if len(sys.argv) > 1 else Action.DO)
