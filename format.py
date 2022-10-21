#!/usr/bin/env python3
# vi: ft=python

from __future__ import annotations

import logging
import multiprocessing
from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor
from logging import Logger
from pathlib import Path
from re import Pattern
from re import compile as RE
from subprocess import CompletedProcess as RunResult
from subprocess import run
from typing import MutableMapping

from common import PROJECT_ROOT, walk

PAT_FMT: MutableMapping[Pattern, type[Formatter]] = {}
LOGFMT: str = "%(asctime)s [%(module)s] [%(levelname)s]: %(message)s"
LOGGER: Logger = logging.getLogger(__name__)


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

        result: RunResult = run([self.EXE, *self.ARGS, *files], capture_output=True)
        result.check_returncode()

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
    MATCH: set[Pattern] = {RE(r".*\.(ba|z)?sh(env|rc)?$")}
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
    MATCH: set[Pattern] = {RE(r".*\.ya?ml(fmt)?$")}


def main() -> None:
    to_fmt: MutableMapping[type[Formatter], set[Path]] = defaultdict(lambda: set())

    patterns: set[Pattern] = set(PAT_FMT.keys())
    for path in walk(PROJECT_ROOT):
        for pattern in patterns:
            if pattern.match(str(path)):
                to_fmt[PAT_FMT[pattern]].add(path)

    futures: set[Future] = set()
    with ThreadPoolExecutor(multiprocessing.cpu_count()) as tpe:
        for formatter, paths in to_fmt.items():
            futures.add(tpe.submit(formatter, *paths))  # type: ignore


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=LOGFMT)
    main()
