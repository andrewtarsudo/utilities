# -*- coding: utf-8 -*-
from click.core import Context as Context
from typing import Iterable
from utilities.common.shared import StrPath as StrPath

RUSSIAN_CHARS: str


def wrap_text(value: str, *, is_color: bool = True, is_success: bool = False): ...


def wrap_iterable(values: Iterable[str], *, is_color: bool = True, is_success: bool = False): ...


def find_first_russian_char(line: str): ...


def file_inspection(path: str, is_color: bool = True): ...


def check_russian_command(
        ctx: Context,
        files: Iterable[StrPath] = None,
        directory: StrPath = None,
        recursive: bool = True,
        verbose: bool = False,
        keep_logs: bool = False): ...
