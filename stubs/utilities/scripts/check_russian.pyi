# -*- coding: utf-8 -*-
from typing import Iterable

from click.core import Context

from utilities.common.shared import StrPath

RUSSIAN_CHARS: str

def style_iterable(values: Iterable[str], fg: str): ...
def find_first_russian_char(line: str): ...
def file_inspection(path: str, is_color: bool = True): ...
def check_russian_command(
        ctx: Context,
        files: Iterable[StrPath] = None,
        directory: StrPath = None,
        recursive: bool = True,
        verbose: bool = False,
        keep_logs: bool = False): ...
