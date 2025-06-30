# -*- coding: utf-8 -*-
from typing import Iterable

from click.core import Context
from click.decorators import help_option, option, pass_context
from click.types import BOOL, INT, Path as ClickPath
from loguru import logger

from utilities.common.config_file import config_file
from utilities.common.functions import file_reader
from utilities.common.shared import HELP, StrPath
from utilities.scripts.api_group import APIGroup, ConditionalOption
from utilities.scripts.cli import cli
from utilities.common.completion import dir_completion, file_completion
from utilities.scripts.list_files import get_files
from utilities.set_table_cols.analyser import TableAnalyser
from utilities.set_table_cols.file import AsciiDocFile

MAX_SYMBOLS: int = config_file.get_commands("set-table-cols", "max_symbols")
MIN_COLUMN: int = config_file.get_commands("set-table-cols", "min_column")


@cli.command(
    "set-table-cols",
    cls=APIGroup,
    help="Команда для задания ширины столбцам таблиц")
@option(
    "-f", "--file", "files",
    type=ClickPath(
        file_okay=True,
        readable=True,
        resolve_path=True,
        allow_dash=False,
        dir_okay=False),
    help="\b\nФайл для обработки. Может использоваться несколько раз",
    cls=ConditionalOption,
    conditional=["directory"],
    multiple=True,
    required=False,
    metavar="FILE ... FILE",
    shell_complete=file_completion,
    default=config_file.get_commands("set-table-cols", "files"))
@option(
    "-d", "--dir", "directory",
    type=ClickPath(
        file_okay=False,
        resolve_path=True,
        allow_dash=False,
        dir_okay=True),
    help="Директория для обработки",
    cls=ConditionalOption,
    conditional=["files"],
    multiple=False,
    required=False,
    metavar="DIR",
    shell_complete=dir_completion,
    default=config_file.get_commands("set-table-cols", "directory"))
@option(
    "-s", "--max-symbols",
    type=INT,
    help=f"\b\nМаксимальная ширина столбца в символах."
         f"\nПо умолчанию: {MAX_SYMBOLS}."
         f"\nПримечание. Должно быть целым положительным числом",
    multiple=False,
    required=False,
    metavar="WIDTH",
    default=config_file.get_commands("set-table-cols", "max_symbols"))
@option(
    "-c", "--min-column",
    type=INT,
    help=f"\b\nМинимальная ширина столбца в символах."
         f"\nПо умолчанию: {MIN_COLUMN}."
         f"\nПримечание. Должно быть целым положительным числом",
    multiple=False,
    required=False,
    metavar="WIDTH",
    default=config_file.get_commands("set-table-cols", "min_column"))
@option(
    "-o/-O", "--add-options/--no-options", "add_options",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг добавления опций таблицы."
         "\nПо умолчанию: True, добавляются:"
         "\n* options=\"header\";"
         "\n* width=\"100%\"",
    show_default=True,
    required=False,
    default=config_file.get_commands("set-table-cols", "add_options"))
@option(
    "-r/-R", "--recursive/--no-recursive",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг рекурсивного поиска файлов."
         "\nПо умолчанию: True, вложенные файлы учитываются",
    show_default=True,
    required=False,
    default=config_file.get_commands("set-table-cols", "recursive"))
@option(
    "-k/-K", "--keep-logs/--remove-logs",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг сохранения директории с лог-файлом по завершении"
         "\nработы в штатном режиме."
         "\nПо умолчанию: False, лог-файл и директория удаляются",
    show_default=True,
    required=False,
    default=config_file.get_commands("set-table-cols", "keep_logs"))
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
@pass_context
def set_table_cols_command(
        ctx: Context,
        files: Iterable[StrPath] = None,
        directory: StrPath = None,
        recursive: bool = True,
        max_symbols: int = MAX_SYMBOLS,
        min_column: int = MIN_COLUMN,
        add_options: bool = True,
        keep_logs: bool = False):
    if add_options:
        options: dict[str, str] | None = {
            "width": "100%",
            "options": "header"}

    else:
        options: dict[str, str] | None = None

    files: list[StrPath] | None = get_files(
        ctx,
        files=files,
        directory=directory,
        recursive=recursive,
        extensions="adoc")

    if files is not None and files:
        table_analyser: TableAnalyser = TableAnalyser(max_symbols=max_symbols, min_column=min_column)

        for file in files:
            logger.debug(f"Файл {file}")
            content: list[str] = file_reader(file, "lines", encoding="utf-8")
            ascii_doc_file: AsciiDocFile = AsciiDocFile(file, content=content)
            ascii_doc_file.set_tables()
            ascii_doc_file.fix_tables(table_analyser, options)
            ascii_doc_file.replace_tables()
            ascii_doc_file.save()

            logger.info(f"Файл {file} обработан и сохранен")

    ctx.obj["keep_logs"] = keep_logs
