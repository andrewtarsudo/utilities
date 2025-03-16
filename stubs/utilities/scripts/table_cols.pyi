# -*- coding: utf-8 -*-
from click.core import Context as Context
from typing import Iterable
from utilities.common.shared import HELP as HELP, MAX_SYMBOLS as MAX_SYMBOLS, MIN_COLUMN as MIN_COLUMN, \
    StrPath as StrPath
from utilities.common.functions import ReaderMode as ReaderMode, file_reader as file_reader
from utilities.scripts.cli import APIGroup as APIGroup, clear_logs as clear_logs, \
    cli as command_line_interface
from utilities.scripts.list_files import get_files as get_files
from utilities.table_cols import TableAnalyser as TableAnalyser
from utilities.table_cols.file import AsciiDocFile as AsciiDocFile


def table_cols_command(
        ctx: Context,
        files: Iterable[StrPath] = None,
        directory: StrPath = None,
        recursive: bool = True,
        max_symbols: int = ...,
        min_column: int = ...,
        keep_logs: bool = False): ...
