# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Iterable

from utilities.common.shared import FileType, ReaderMode, StrPath


def get_version(): ...


def file_reader(path: StrPath, reader_mode: ReaderMode, *, encoding: str = 'utf-8'): ...


def file_writer(path: StrPath, content: str | Iterable[str], *, encoding: str = 'utf-8'): ...


def file_reader_type(path: StrPath, file_type: FileType): ...


def check_path(
        path: StrPath,
        ignored_dirs: Iterable[str] = None,
        ignored_files: Iterable[str] = None,
        extensions: Iterable[str] = None,
        language: str | None = None): ...


def walk_full(
        path: StrPath, *,
        ignored_dirs: Iterable[str] = None,
        ignored_files: Iterable[str] = None,
        extensions: Iterable[str] = None,
        language: str | None = None,
        root: Path = None,
        results: list[Path] = None): ...


def pretty_print(values: Iterable[StrPath] = None): ...
