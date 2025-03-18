# -*- coding: utf-8 -*-
from click.core import Context as Context
from typing import Iterable
from utilities.common.shared import ADOC_EXTENSION as ADOC_EXTENSION, HELP as HELP, MD_EXTENSION as MD_EXTENSION, \
    StrPath as StrPath, pretty_print as pretty_print
from utilities.common.errors import FormatCodeNonIntegerLineLengthError as FormatCodeNonIntegerLineLengthError, \
    FormatCodeNonPositiveLineLengthError as FormatCodeNonPositiveLineLengthError
from utilities.common.functions import ReaderMode as ReaderMode, file_reader as file_reader, file_writer as file_writer
from utilities.scripts.cli import APIGroup as APIGroup, clear_logs as clear_logs, \
    cli as cli
from utilities.scripts.list_files import get_files as get_files

MAX_LENGTH: int


def format_code_command(
        ctx: Context,
        directory: StrPath = None,
        files: Iterable[StrPath] = None,
        recursive: bool = True,
        length: int = ...,
        keep_logs: bool = False): ...


def split(line: str, start: int = 0, length: int = ..., split_lines: Iterable[str] = None) -> list[str] | None: ...
