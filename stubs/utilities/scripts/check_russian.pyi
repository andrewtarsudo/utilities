# -*- coding: utf-8 -*-
from click.core import Context as Context
from typing import Iterable
from utilities.common.shared import FAIL_COLOR as FAIL_COLOR, HELP as HELP, NORMAL_COLOR as NORMAL_COLOR, \
    PASS_COLOR as PASS_COLOR, StrPath as StrPath, pretty_print as pretty_print, separator as separator
from utilities.common.functions import ReaderMode as ReaderMode, file_reader as file_reader
from utilities.scripts.cli import APIGroup as APIGroup, clear_logs as clear_logs, \
    cli as command_line_interface
from utilities.scripts.list_files import get_files as get_files

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
