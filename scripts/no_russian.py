# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Iterable

from click.core import Context
from click.decorators import help_option, option, pass_context
from click.termui import pause
from click.utils import echo
from click.types import BOOL, Path as ClickPath

from common.constants import FAIL_COLOR, HELP, NORMAL_COLOR, PASS_COLOR, PRESS_ENTER_KEY
from common.functions import get_files
from scripts.cli import APIGroup, command_line_interface

RUSSIAN_CHARS: str = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
NAME: str = Path(__file__).name


@command_line_interface.command(
    "check-russian",
    cls=APIGroup,
    help="Команда для проверки наличия непереведенных слов",
    invoke_without_command=True)
@option(
    "-f", "--file", "files",
    type=ClickPath(
        exists=True,
        file_okay=True,
        readable=True,
        resolve_path=True,
        allow_dash=False,
        dir_okay=False),
    help="Файл для обработки.\nМожет использоваться несколько раз",
    multiple=True,
    required=False,
    metavar="<FILE> ... <FILE>",
    default=None
)
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
    metavar="<DIR>",
    default=None
)
@option(
    "--recursive/--no-recursive",
    type=BOOL,
    is_flag=True,
    help="Флаг рекурсивного поиска файлов.\nПо умолчанию: True",
    show_default=True,
    required=False,
    default=True)
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
@pass_context
def check_no_russian_command(
        ctx: Context,
        files: Iterable[str | Path] = None,
        directory: str | Path = None,
        recursive: bool = True):
    files: list[str | Path] | None = get_files(files, directory, recursive)

    if files is None:
        pause(PRESS_ENTER_KEY)
        ctx.exit(0)

    result: list[str] = []

    for file in files:
        _indexes: list[str] = []

        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            _indexes.extend(
                f"{index + 1}" for index, line in enumerate(f.readlines())
                if any(char in line for char in RUSSIAN_CHARS))

        if not _indexes:
            result.append(
                f"{PASS_COLOR}В файле {file} не найдены кириллические буквы{NORMAL_COLOR}")

        else:
            result.append(
                f"{FAIL_COLOR}В файле {file} найдены кириллические буквы в строках: "
                f"{', '.join(_indexes)}{NORMAL_COLOR}")

    echo("\n".join(result))

    pause(PRESS_ENTER_KEY)
    ctx.exit(0)
