# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Any, Iterable, Mapping, NamedTuple

from click.core import Context

from utilities.common.shared import StrPath

EPILOG: str


def determine_key(item: Mapping, keys: Iterable[str]): ...


def detect_extra_keys(item: Mapping[str, Any]): ...


def rel(path: Path, root: Path): ...


def fix_path(ctx: Context, line_no: int, path: Path, root: Path): ...


class GeneralInfo(NamedTuple):
    messages: list[str] = ...
    warnings: list[str] = ...
    options: list[str] = ...
    names: set[str] = ...
    non_unique_names: set[str] = ...

    def clear(self) -> None: ...


general_info: GeneralInfo


def inspect_settings(content: Mapping[str, Any], verbose: bool): ...


def inspect_legal(content: Mapping[str, Any], verbose: bool): ...


def inspect_sections(content: Mapping[str, Any], verbose: bool): ...


def find_non_unique(lines: list[str]): ...


def validate_file(
        root: StrPath,
        lines: Iterable[str], *,
        output: str | None = None,
        guess: bool = True,
        verbose: bool = False): ...


def validate_yaml_command(
        ctx: Context,
        file_or_project: StrPath,
        output: StrPath = None,
        guess: bool = True,
        verbose: bool = False,
        keep_logs: bool = False): ...
