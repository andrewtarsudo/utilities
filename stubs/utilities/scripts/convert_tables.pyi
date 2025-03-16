# -*- coding: utf-8 -*-
from click.core import Context as Context
from utilities.common.shared import HELP as HELP, StrPath as StrPath
from utilities.convert_tables.line_formatter import LineFormatter as LineFormatter
from utilities.convert_tables.xml_file import CoreDocument as CoreDocument, XmlDocument as XmlDocument
from utilities.scripts.cli import MutuallyExclusiveOption as MutuallyExclusiveOption, \
    SwitchArgsAPIGroup as SwitchArgsAPIGroup, clear_logs as clear_logs, cli as command_line_interface


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
