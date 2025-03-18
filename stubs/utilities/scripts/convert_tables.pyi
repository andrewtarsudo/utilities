# -*- coding: utf-8 -*-
from click.core import Context as Context
from utilities.common.shared import StrPath as StrPath


def convert_tables_command(
        ctx: Context,
        docx_file: StrPath,
        tables_dir: StrPath = './tables/',
        temp_dir: StrPath = './_temp/',
        remove: bool = False,
        escape: bool = True,
        fix: bool = None,
        keep: bool = None,
        keep_logs: bool = False): ...
