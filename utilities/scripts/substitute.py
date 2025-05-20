# -*- coding: utf-8 -*-
from re import Match, sub
from typing import Iterable, Mapping

from click import argument
from click.core import Context
from click.decorators import help_option, option, pass_context
from click.types import BOOL, Path as ClickPath
from loguru import logger

from utilities.common.config_file import config_file
from utilities.common.errors import FileReaderTypeError
from utilities.common.functions import file_reader, file_reader_type, file_writer
from utilities.common.shared import FileType, HELP, StrPath
from utilities.common.completion import file_completion
from utilities.scripts.cli import APIGroup, cli
from utilities.scripts.list_files import get_files


def substitute(replace_table: Mapping[str, str], file: StrPath, dry_run: bool = False):
    logger.debug(f"Обработка файла {file}:")

    lines: list[str] = file_reader(file, "lines")

    def repl(m: Match):
        if m.group(1) in replace_table:
            substitution: str = replace_table.get(m.group(1))
            logger.debug(f"Замена {m.group(1)} -> {substitution}")
            return substitution

        else:
            logger.debug(f"{m.group(1)} нет в таблице замен")
            return m.group(1)

    lines: list[str] = [sub(r"(\{.+?})", repl, line) for line in iter(lines)]

    if not dry_run:
        file_writer(file, lines)

    logger.info(f"Обработка файла {file} завершена\n")


@cli.command(
    "substitute",
    cls=APIGroup,
    help="Команда для замены переменных на их значения")
@argument(
    "file_table",
    type=ClickPath(
        file_okay=True,
        readable=True,
        resolve_path=True,
        allow_dash=False,
        dir_okay=False),
    required=True,
    shell_complete=file_completion,
    metavar="FILE_TABLE")
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
    default=config_file.get_commands("substitute", "files"))
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
    default=config_file.get_commands("substitute", "directory"))
@option(
    "--dry-run/--no-dry-run",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг вывода изменений файлов без их изменения.\n"
         "По умолчанию: False, файлы перезаписываются",
    show_default=True,
    required=False,
    default=config_file.get_commands("substitute", "dry_run"))
@option(
    "-r/-R", "--recursive/--no-recursive",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг рекурсивного поиска файлов."
         "\nПо умолчанию: True, вложенные файлы учитываются",
    show_default=True,
    required=False,
    default=config_file.get_commands("substitute", "recursive"))
@option(
    "-k/-K", "--keep-logs/--remove-logs",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг сохранения директории с лог-файлом по завершении"
         "\nработы в штатном режиме."
         "\nПо умолчанию: False, лог-файл и директория удаляются",
    show_default=True,
    required=False,
    default=config_file.get_commands("substitute", "keep_logs"))
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
@pass_context
def substitute_command(
        ctx: Context,
        file_table: StrPath,
        files: Iterable[StrPath] = None,
        directory: StrPath = None,
        recursive: bool = True,
        dry_run: bool = False,
        keep_logs: bool = False):
    files: list[StrPath] | None = get_files(
        ctx,
        files=files,
        directory=directory,
        recursive=recursive,
        extensions="adoc")

    if file_table.suffix in (".json", ".json5"):
        file_type: FileType = "json"

    elif file_table.suffix in (".yaml", ".yml"):
        file_type: FileType = "yaml"

    elif file_table.suffix == ".toml":
        file_type: FileType = "toml"

    else:
        raise FileReaderTypeError

    replace_table: dict[str, str] = file_reader_type(file_table, file_type)

    if files is not None and files:
        for file in iter(files):
            substitute(replace_table, file, dry_run)

    ctx.obj["keep_logs"] = keep_logs
