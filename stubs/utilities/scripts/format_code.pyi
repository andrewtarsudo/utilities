# -*- coding: utf-8 -*-
from typing import Iterable

from click.core import Context

from utilities.common.shared import StrPath

MAX_LENGTH: int


def format_code_command(
        ctx: Context,
        directory: StrPath = None,
        files: Iterable[StrPath] = None,
        recursive: bool = True,
        length: int = ...,
        keep_logs: bool = False): ...


def split(
        line: str,
        start: int = 0,
        length: int = ...,
        split_lines: Iterable[str] = None) -> list[str] | None: ...
