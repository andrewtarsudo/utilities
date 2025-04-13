# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Any, Iterable

from click.core import Context, Parameter

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
