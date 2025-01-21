# -*- coding: utf-8 -*-
from os import system
from sys import platform
from typing import Iterable

from click.core import Context
from click.decorators import help_option, option, pass_context
from click.types import BOOL, Path as ClickPath
from click.utils import echo

from utilities.common.constants import FAIL_COLOR, HELP, NORMAL_COLOR, PASS_COLOR, StrPath
from utilities.common.functions import get_files
from utilities.scripts import APIGroup
from utilities.scripts.cli import clear_logs, command_line_interface

RUSSIAN_CHARS: str = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"


@command_line_interface.command(
    "check-russian",
    cls=APIGroup,
    help="Команда для проверки наличия непереведенных слов")
@option(
    "-d", "--dir", "directory",
    type=ClickPath(
        exists=True,
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
    "-f", "--file", "files",
    type=ClickPath(
        exists=True,
        file_okay=True,
        readable=True,
        resolve_path=True,
        allow_dash=False,
        dir_okay=False),
    help="\b\nПеречень файлов для обработки.\nМожет использоваться несколько раз",
    multiple=True,
    required=False,
    metavar="FILE ... FILE",
    default=None)
@option(
    "--recursive/--no-recursive",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг рекурсивного поиска файлов.\nПо умолчанию: True, поиск файлов по вложенным папкам",
    show_default=True,
    required=False,
    default=True)
@option(
    "--verbose/--no-verbose",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг подробного вывода.\nПо умолчанию: False, выводятся только ошибки",
    show_default=True,
    required=False,
    default=False)
@option(
    "--keep-logs",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг сохранения директории с лог-файлом по завершении \nработы в штатном режиме.\n"
         "По умолчанию: False, лог-файл и директория удаляются",
    show_default=True,
    required=False,
    default=False)
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
@pass_context
def check_russian_command(
        ctx: Context,
        files: Iterable[StrPath] = None,
        directory: StrPath = None,
        recursive: bool = True,
        verbose: bool = False,
        keep_logs: bool = False):
    if platform.startswith("win"):
        system("color")

    files: list[StrPath] | None = get_files(
        ctx,
        files=files,
        directory=directory,
        recursive=recursive,
        language="en")

    if files is not None:
        result: list[str] = []

        for file in files:
            _indexes: list[str] = []

            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                _indexes.extend(
                    f"{index + 1}" for index, line in enumerate(f.readlines())
                    if any(char in line for char in RUSSIAN_CHARS))

            if not _indexes and verbose:
                result.append(
                    f"{PASS_COLOR}В файле {file} не найдены кириллические буквы{NORMAL_COLOR}")

            elif not _indexes:
                continue

            else:
                result.append(
                    f"{FAIL_COLOR}В файле {file} найдены кириллические буквы в строках: "
                    f"{', '.join(_indexes)}{NORMAL_COLOR}")

        if not result:
            result.append(f"{PASS_COLOR}Ни в одном файле не обнаружены кириллические символы{NORMAL_COLOR}")

        echo("\n".join(result))

    ctx.obj["keep_logs"] = keep_logs
    ctx.invoke(clear_logs)
