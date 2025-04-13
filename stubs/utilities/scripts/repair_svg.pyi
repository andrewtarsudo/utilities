# -*- coding: utf-8 -*-
from typing import Iterable

from click.core import Context

from utilities.common.shared import StrPath


def repair_svg_command(
        ctx: Context,
        files: Iterable[StrPath] = None,
        directory: StrPath = None,
        recursive: bool = True,
        keep_logs: bool = False): ...
