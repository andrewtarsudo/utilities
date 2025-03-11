# -*- coding: utf-8 -*-
from pathlib import Path

from click.core import Context
from loguru import logger
from typer.main import Typer
from typer.params import Option
from typing_extensions import Annotated, List

from utilities.common.constants import MAX_SYMBOLS, MIN_COLUMN, StrPath
from utilities.common.functions import file_reader, ReaderMode
from utilities.scripts.cli import clear_logs
from utilities.scripts.list_files import get_files
from utilities.table_cols import TableAnalyser
from utilities.table_cols.file import AsciiDocFile

table_cols: Typer = Typer()


@table_cols.command(
    name="table-cols",
    help="Команда для задания ширины столбцам таблиц")
def table_cols_command(
        ctx: Context,
        files: Annotated[
            List[Path],
            Option(
                "--file", "-f",
                help="Файл для обработки. Может использоваться несколько раз",
                metavar="FILE .. FILE",
                exists=True,
                file_okay=True,
                dir_okay=False,
                resolve_path=True,
                allow_dash=False)] = None,
        directory: Annotated[
            Path,
            Option(
                "--dir", "-d",
                help="Директория для обработки",
                exists=True,
                file_okay=False,
                dir_okay=True,
                resolve_path=True,
                allow_dash=False)] = None,
        recursive: Annotated[
            bool,
            Option(
                "--recursive/--no-recursive", "-r/-R",
                show_default=True,
                help="Флаг рекурсивного поиска файлов.\nПо умолчанию: True, вложенные файлы учитываются")] = True,
        max_symbols: Annotated[
            int,
            Option(
                "-s", "--max-symbols",
                metavar="WIDTH",
                help=f"Максимальная ширина столбца в символах."
                     f"\nПо умолчанию: {MAX_SYMBOLS}."
                     f"\nПримечание. Должно быть целым положительным числом",
                show_default=True)] = MAX_SYMBOLS,
        min_column: Annotated[
            int,
            Option(
                "-c", "--min-column",
                metavar="WIDTH",
                help=f"Минимальная ширина столбца в символах."
                     f"\nПо умолчанию: {MIN_COLUMN}."
                     f"\nПримечание. Должно быть целым положительным числом",
                show_default=True)] = MIN_COLUMN,
        keep_logs: Annotated[
            bool,
            Option(
                "--keep-logs",
                show_default=True,
                help="Флаг сохранения директории с лог-файлом по завершении\nработы в штатном режиме."
                     "\nПо умолчанию: False, лог-файл и директория удаляются")] = False):
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
