#!/usr/bin/env python3
# vi: ft=python

from __future__ import annotations
from concurrent.futures import Future, ThreadPoolExecutor

import logging
import multiprocessing
from os import dup
import shutil
from abc import ABCMeta
from logging import Logger
from pathlib import Path
from subprocess import PIPE, STDOUT, Popen
from typing import IO, Any, Mapping, MutableMapping, cast

from common import PROJECT_ROOT, walk

EXT_FMT: MutableMapping[str, type[Formatter]] = {}
IGNORE: set[str] = {".git", ".mypy_cache", "__pycache__"}
LOGFMT: str = "%(asctime)s [%(module)s] [%(levelname)s] %(formatter)s: %(message)s"
LOGGER: Logger = logging.getLogger(__name__)


class Singleton(ABCMeta):
    _instance = None

    def __call__(self: Singleton, *args: list[Any], **kwds: Mapping[str, Any]) -> Any:
        if self._instance is None:
            self._instance = super().__call__(*args, **kwds)

        return self._instance


class Formatter(metaclass=Singleton):
    EXTS: set[str]
    EXE: str
    ARGS: list[str] = []

    def _check_exe(self: Formatter):
        if not shutil.which(self.EXE):
            raise RuntimeError(f"{self.EXE} was not found on $PATH!")

    def __init_subclass__(cls: type[Formatter]) -> None:
        for ext in cls.EXTS:
            EXT_FMT[ext] = cls

    def __init__(self: Formatter) -> None:
        self._check_exe()
        print([self.EXE, *self.ARGS])
        self._proc: Popen = Popen([self.EXE, *self.ARGS], stdin=PIPE, stdout=PIPE)
        self._proc_stdin: IO[bytes] = cast(IO[bytes], self._proc.stdin)
        self._proc_sdout: IO[bytes] = cast(IO[bytes], self._proc.stdout)
        self._proc_stderr: IO[bytes] = cast(IO[bytes], self._proc.stderr)

    def __call__(self, file: Path) -> Any:
        LOGGER.info(f"formatting {file}", extra=dict(formatter=self.__class__.__name__))
        with file.open("rb+") as fd:
            self._proc_stdin.write(fd.read())
            print(self._proc_sdout.read())


class YAML(Formatter):
    EXTS: set[str] = {"yml", "yaml"}
    EXE: str = "yamlfmt"
    ARGS: list[str] = ["-"]


class Lua(Formatter):
    EXE: str = "stylua"
    EXTS: set[str] = {"lua"}
    ARGS: list[str] = ["-"]


def fmt(file: Path) -> None:
    ext: str = file.suffix.lstrip(".")
    if ext in EXT_FMT:
        EXT_FMT[ext]()(file)


def main() -> None:
    for file in walk(PROJECT_ROOT / "home"):
        fmt(file.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=LOGFMT)
    main()
