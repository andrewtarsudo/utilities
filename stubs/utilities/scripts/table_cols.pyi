# -*- coding: utf-8 -*-
from typing import Iterable

from click.core import Context

from utilities.common.shared import StrPath


def table_cols_command(
        ctx: Context,
        files: Iterable[StrPath] = None,
        directory: StrPath = None,
        recursive: bool = True,
        max_symbols: int = ...,
        min_column: int = ...,
        add_options: bool = True,
        keep_logs: bool = False): ...
