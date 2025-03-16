# -*- coding: utf-8 -*-
from click.core import Context as Context
from typing import Iterable
from utilities.common.shared import HELP as HELP, StrPath as StrPath, separator as separator
from utilities.scripts.cli import APIGroup as APIGroup, clear_logs as clear_logs, \
    cli as command_line_interface
from utilities.scripts.list_files import get_files as get_files


def file_size(value: int) -> str: ...


def duplicate_image(file: StrPath, dry_run: bool = False) -> StrPath: ...


def reduce_image_command(
        ctx: Context,
        files: Iterable[StrPath] = None,
        directory: StrPath = None,
        recursive: bool = True,
        dry_run: bool = False,
        keep_logs: bool = False): ...
