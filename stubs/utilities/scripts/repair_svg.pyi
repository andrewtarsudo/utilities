# -*- coding: utf-8 -*-
from click.core import Context as Context
from typing import Iterable
from utilities.common.shared import StrPath as StrPath


def repair_svg_command(
        ctx: Context,
        files: Iterable[StrPath] = None,
        directory: StrPath = None,
        recursive: bool = True,
        keep_logs: bool = False): ...
