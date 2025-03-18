# -*- coding: utf-8 -*-
from click.core import Context as Context
from pathlib import Path
from utilities.common.shared import StrPath as StrPath


def validate_dir_path(path: StrPath | None) -> bool: ...


def has_no_required_files(path: StrPath) -> bool: ...


def link_repair_command(
        ctx: Context,
        pathdir: Path,
        dry_run: bool = False,
        no_result: bool = False,
        anchor_validation: bool = True,
        separate_languages: bool = True,
        skip_en: bool = False,
        keep_logs: bool = False): ...
