# -*- coding: utf-8 -*-
from typing import Iterable

from click.core import Context
from click.decorators import help_option, option, pass_context
from click.types import BOOL, INT, Path as ClickPath
from loguru import logger

from utilities.common.constants import HELP, MAX_SYMBOLS, MIN_COLUMN, StrPath
from utilities.common.functions import file_reader, ReaderMode
from utilities.scripts.cli import APIGroup, clear_logs, command_line_interface
from utilities.scripts.list_files import get_files
from utilities.table_cols import TableAnalyser
from utilities.table_cols.file import AsciiDocFile


@command_line_interface.command(
    "table-cols",
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
    multiple=True,
    required=False,
    metavar="FILE ... FILE",
    default=None)
@option(
    "-d", "--dir", "directory",
    type=ClickPath(
        file_okay=False,
        resolve_path=True,
        allow_dash=False,
        dir_okay=True),
    help="Директория для обработки",
    multiple=False,
    required=False,
    metavar="DIR",
    default=None)
@option(
    "-s", "--max-symbols",
    type=INT,
    help=f"\b\nМаксимальная ширина столбца в символах."
         f"\nПо умолчанию: {MAX_SYMBOLS}."
         f"\nПримечание. Должно быть целым положительным числом",
    multiple=False,
    required=False,
    metavar="WIDTH",
    default=MAX_SYMBOLS)
@option(
    "-c", "--min-column",
    type=INT,
    help=f"\b\nМинимальная ширина столбца в символах."
         f"\nПо умолчанию: {MIN_COLUMN}."
         f"\nПримечание. Должно быть целым положительным числом",
    multiple=False,
    required=False,
    metavar="WIDTH",
    default=MIN_COLUMN)
@option(
    "--recursive/--no-recursive", "-r/-R",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг рекурсивного поиска файлов."
         "\nПо умолчанию: True, вложенные файлы учитываются",
    show_default=True,
    required=False,
    default=True)
@option(
    "--keep-logs/--remove-logs", "-k/-K",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг сохранения директории с лог-файлом по завершении"
         "\nработы в штатном режиме."
         "\nПо умолчанию: False, лог-файл и директория удаляются",
    show_default=True,
    required=False,
    default=False)
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
@pass_context
def table_cols_command(
        ctx: Context,
        files: Iterable[StrPath] = None,
        directory: StrPath = None,
        recursive: bool = True,
        max_symbols: int = MAX_SYMBOLS,
        min_column: int = MIN_COLUMN,
        keep_logs: bool = False):
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
            content: list[str] = file_reader(file, ReaderMode.LINES, encoding="utf-8")
            ascii_doc_file: AsciiDocFile = AsciiDocFile(file, content=content)
            ascii_doc_file.set_tables()
            ascii_doc_file.fix_tables(table_analyser)
            ascii_doc_file.replace_tables()
            ascii_doc_file.save()

            logger.info(f"Файл {file} обработан и сохранен")

    ctx.obj["keep_logs"] = keep_logs
    ctx.invoke(clear_logs)
