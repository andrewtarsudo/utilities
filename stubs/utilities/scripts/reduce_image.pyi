# -*- coding: utf-8 -*-
from click.core import Context as Context
from typing import Iterable
from utilities.common.shared import StrPath as StrPath


def file_size(value: int) -> str: ...


def duplicate_image(file: StrPath, dry_run: bool = False) -> StrPath: ...


def reduce_image_command(
        ctx: Context,
        files: Iterable[StrPath] = None,
        directory: StrPath = None,
        recursive: bool = True,
        dry_run: bool = False,
        keep_logs: bool = False): ...
