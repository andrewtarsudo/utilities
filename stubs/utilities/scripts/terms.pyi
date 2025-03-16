# -*- coding: utf-8 -*-
from click.core import Context as Context, Parameter as Parameter
from pathlib import Path
from typing import Any, Iterable
from utilities.common.shared import HELP as HELP, PRESS_ENTER_KEY as PRESS_ENTER_KEY, pretty_print as pretty_print
from utilities.common.functions import ReaderMode as ReaderMode, file_reader as file_reader
from utilities.scripts.cli import APIGroup as APIGroup, MutuallyExclusiveOption as MutuallyExclusiveOption, \
    clear_logs as clear_logs, cli as command_line_interface
from utilities.terms.ascii_doc_table_terms import AsciiDocTableTerms as AsciiDocTableTerms
from utilities.terms.git_manager import git_manager as git_manager
from utilities.terms.table import Term as Term

INFO_FILE: Path
README_FILE: Path
SAMPLES_FILE: Path


def print_file(ctx: Context, param: Parameter, value: Any): ...


def terms_command(
        ctx: Context,
        terms: Iterable[str] = None, *,
        all_flag: bool = False,
        full_flag: bool = False,
        info_flag: bool = False,
        readme_flag: bool = False,
        samples_flag: bool = False,
        abbr_flag: bool = False,
        ascii_flag: bool = False,
        keep_logs: bool = False,
        common_flag: bool = False): ...
