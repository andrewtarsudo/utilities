# -*- coding: utf-8 -*-
from pathlib import Path

from click.core import Context

from utilities.common.shared import StrPath


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
