# -*- coding: utf-8 -*-
from click.core import Context as Context
from pathlib import Path
from utilities.common.shared import ADOC_EXTENSION as ADOC_EXTENSION, HELP as HELP, MD_EXTENSION as MD_EXTENSION, \
    PRESS_ENTER_KEY as PRESS_ENTER_KEY, StrPath as StrPath
from utilities.common.errors import LinkRepairInvalidFileDictAttributeError as LinkRepairInvalidFileDictAttributeError, \
    LinkRepairInvalidStorageAttributeError as LinkRepairInvalidStorageAttributeError
from utilities.common.functions import ReaderMode as ReaderMode, file_reader as file_reader, file_writer as file_writer
from utilities.link_repair.const import FileLanguage as FileLanguage, prepare_logging as prepare_logging
from utilities.link_repair.file_dict import FileDict as FileDict, FileLinkItem as FileLinkItem, TextFile as TextFile
from utilities.link_repair.general_storage import Storage as Storage
from utilities.link_repair.internal_link_inspector import internal_inspector as internal_inspector
from utilities.link_repair.link import Link as Link
from utilities.link_repair.link_fixer import link_fixer as link_fixer
from utilities.link_repair.link_inspector import link_inspector as link_inspector
from utilities.scripts.cli import SwitchArgsAPIGroup as SwitchArgsAPIGroup, clear_logs as clear_logs, \
    cli as command_line_interface


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
