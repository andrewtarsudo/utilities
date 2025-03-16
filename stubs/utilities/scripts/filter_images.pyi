# -*- coding: utf-8 -*-
from click.core import Context as Context
from pathlib import Path
from utilities.common.shared import HELP as HELP, StrPath as StrPath, pretty_print as pretty_print
from utilities.common.functions import ReaderMode as ReaderMode, file_reader as file_reader, file_writer as file_writer
from utilities.scripts.cli import SwitchArgsAPIGroup as SwitchArgsAPIGroup, clear_logs as clear_logs, \
    cli as command_line_interface
from utilities.scripts.list_files import get_files as get_files


class File:
    pattern: str

    def __init__(self, path: StrPath) -> None: ...

    def __iter__(self): ...

    def __bool__(self) -> bool: ...

    @property
    def full_links(self) -> list[Path]: ...

    def fix_link(self, link: str): ...


class MdFile(File):
    pattern: str

    @property
    def full_links(self): ...


class AsciiDocFile(File):
    pattern: str

    @property
    def imagesdir(self): ...

    @property
    def full_links(self): ...


def filter_images_command(
        ctx: Context,
        project_dir: StrPath,
        dry_run: bool = False,
        output: StrPath = None,
        recursive: bool = True,
        keep_logs: bool = False): ...
