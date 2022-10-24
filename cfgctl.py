#!/usr/bin/env python3
# vi: ft=python

from __future__ import annotations

import logging
import multiprocessing
import sys
from argparse import ArgumentParser, Namespace
from argparse import _SubParsersAction as SubParsersAction
from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor
from enum import Enum, unique
from logging import Logger
from pathlib import Path
from re import Pattern
from re import compile as RE
from subprocess import CompletedProcess as RunResult
from subprocess import run
from typing import Any, MutableMapping

PROG: str = Path(__file__).stem
DEFAULT_DIR_MODE: int = 0o700
IGNORE: set[str] = {".git", ".mypy_cache", "__pycache__"}
LOGFMT: str = "%(asctime)s [%(module)s] [%(levelname)s]: %(message)s"
LOGGER: Logger = logging.getLogger(__name__)
PAT_FMT: MutableMapping[Pattern, type[Formatter]] = {}
PROJECT_ROOT: Path = Path(__file__).parent
SYMLINK_ROOT: Path = Path.home()


def walk(path: Path):
    for p in Path(path).iterdir():
        if set(p.parts) & IGNORE:
            continue

        if p.is_dir():
            yield from walk(p)
            continue

        yield p


class Formatter:
    EXE: str
    ARGS: list[str] = []
    STDOUT: bool = False
    MATCH: set[Pattern]

    def __init_subclass__(cls: type[Formatter]) -> None:
        for pat in cls.MATCH:
            PAT_FMT[pat] = cls

    def __init__(self: Formatter, *files: Path) -> None:
        LOGGER.info(
            f"Running {self.__class__.__name__} ({self.EXE}) with {[f.name for f in files]}"
        )

        if self.STDOUT:
            for file in files:
                with file.open("rb+") as fd:
                    single: RunResult = run(
                        [self.EXE, *self.ARGS, file], capture_output=True
                    )
                    single.check_returncode()
                    fd.truncate()
                    fd.write(single.stdout)

            return

        result: RunResult = run(
            [self.EXE, *self.ARGS, *[str(f) for f in files]], capture_output=True
        )

        if not self.STDOUT and result.stdout:
            for line in result.stdout.splitlines():
                LOGGER.info(
                    f"{self.__class__.__name__} > {self.EXE} stdout: {line.decode()}"
                )

        if result.stderr:
            for line in result.stderr.splitlines():
                LOGGER.info(
                    f"{self.__class__.__name__} > {self.EXE} stderr: {line.decode()}"
                )

        # result.check_returncode()


class JSON(Formatter):
    EXE: str = "jq"
    ARGS: list[str] = ["."]
    MATCH: set[Pattern] = {RE(r".*\.json$")}
    STDOUT: bool = True


class Lua(Formatter):
    EXE: str = "stylua"
    MATCH: set[Pattern] = {RE(r".*\.lua$")}


class Python(Formatter):
    EXE: str = "black"
    MATCH: set[Pattern] = {RE(r".*\.py$")}


class Shell(Formatter):
    EXE: str = "shfmt"
    MATCH: set[Pattern] = {RE(r".*\.(ba|z)?sh$")}
    ARGS: list[str] = ["-i=2", "-w"]


class TOML(Formatter):
    EXE: str = "tomll"
    MATCH: set[Pattern] = {RE(r".*\.toml$")}


class XML(Formatter):
    EXE: str = "xmllint"
    MATCH: set[Pattern] = {RE(r".*\.plist$")}
    STDOUT: bool = True


class YAML(Formatter):
    EXE: str = "yamlfmt"
    MATCH: set[Pattern] = {RE(r".*\.ya?ml$")}
    ARGS: list[str] = [
        "-conf",
        str((Path(PROJECT_ROOT) / ".yamlfmt").relative_to(PROJECT_ROOT)),
    ]


def fmtsrcs(root: Path = PROJECT_ROOT) -> None:
    to_fmt: MutableMapping[type[Formatter], set[Path]] = defaultdict(lambda: set())

    patterns: set[Pattern] = set(PAT_FMT.keys())
    for path in walk(root):
        for pattern in patterns:
            if pattern.match(str(path)):
                to_fmt[PAT_FMT[pattern]].add(path)

    futures: set[Future] = set()
    with ThreadPoolExecutor(multiprocessing.cpu_count()) as tpe:
        for formatter, paths in to_fmt.items():
            futures.add(tpe.submit(formatter, *paths))  # type: ignore

    for f in futures:
        f.result()


@unique
class SymlinkAction(Enum):
    LINK = "link"
    UNLINK = "unlink"


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


def symlink(action: SymlinkAction) -> None:
    futures: set[Future] = set()
    home_tree: Path = PROJECT_ROOT / "home"

    with ThreadPoolExecutor(multiprocessing.cpu_count()) as tpe:
        for src in walk(home_tree):
            minpath: Path = Path(*src.relative_to(PROJECT_ROOT).parts[1:])

            # fmt: off
            futures.add(tpe.submit(
                link if action == SymlinkAction.LINK else unlink,
                SYMLINK_ROOT / minpath, home_tree / minpath,
            ))
            # fmt: on

    for future in futures:
        result: Any = future.result()
        if result is not None:
            print(result)


def make_parser() -> ArgumentParser:
    parser: ArgumentParser = ArgumentParser(
        PROG,
        f"{PROG} <command> [option...]",
        f"{PROG} - helper to work with this repository",
    )
    command_subparsers: SubParsersAction = parser.add_subparsers(
        title=f"{PROG} commands",
        dest="command",
        description="Components for working with configuration in this repository",
    )
    format_parser: ArgumentParser = command_subparsers.add_parser(
        "format", aliases=["f", "fmt"], help="Format all configured sources"
    )
    symlinks_parser: ArgumentParser = command_subparsers.add_parser(
        "symlinks",
        aliases=["s", "sl", "l", "links"],
        help="Manage symbolic links to configuration files",
    )
    symlinks_actions_subparser: SubParsersAction = symlinks_parser.add_subparsers(
        title="symlink management actions",
        dest="symlinks_action",
        description="Actions for workign with symbolic links",
    )
    create_symlinks_parer: ArgumentParser = symlinks_actions_subparser.add_parser(
        "create", aliases=["c"], help="Create symbolic links to this repository"
    )
    remove_symlinks_parser: ArgumentParser = symlinks_actions_subparser.add_parser(
        "remove",
        aliases=["r"],
        help="Remove symbolic links to this repository",
    )

    return parser


def main(argv: list[str]) -> None:
    parser: ArgumentParser = make_parser()
    args: Namespace = parser.parse_args(argv)
    if not argv:
        parser.print_help()

    if args.command in {"format", "fmt", "f"}:
        fmtsrcs()

    if args.command in {"symlinks", "links", "sl", "l"}:
        print("hi")
        symlink(
            SymlinkAction.LINK
            if args.symlinks_action in {"create", "c"}
            else SymlinkAction.UNLINK
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=LOGFMT)
    main(sys.argv[1:])
