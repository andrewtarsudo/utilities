# -*- coding: utf-8 -*-
from pathlib import Path
from re import finditer, Match
from typing import Iterable

from click.core import Context
from click.decorators import help_option, option, pass_context
from click.termui import pause
from click.types import BOOL, INT, Path as ClickPath
from loguru import logger

from common.constants import HELP, PRESS_ENTER_KEY
from common.functions import get_files
from scripts.cli import APIGroup, command_line_interface

MAX_LENGTH: int = 84


def split(
        line: str,
        start: int = 0,
        length: int = MAX_LENGTH,
        split_lines: Iterable[str] = None) -> list[str] | None:
    if split_lines is None:
        split_lines: list[str] = []
    else:
        split_lines: list[str] = [*split_lines]

    if len(line) <= length:
        split_lines.append(line)
        return split_lines

    while start < len(line) - 1:
        end: int = min(start + length, len(line))

        _slice: str = line[start:end]

        if end < len(line):
            _matches: list[Match] = list(finditer(";", _slice))

            if not _matches:
                stop_br: int = _slice.rfind("[")
                stop_comma: int = _slice.rfind(",")

                stop: int = max(stop_br, stop_comma)

                if stop == -1:
                    stop: int = len(_slice) - 1

            else:
                _last: Match = _matches[-1]
                stop: int = _last.end()

            if stop <= 0:
                logger.error("Ошибка разбиения файла на части")
                raise OSError

        else:
            stop: int = len(line) - start

        split_line: str = line[start:start + stop]
        split_lines.append(split_line)

        start += stop

        split(line, start, length, split_lines)

    else:
        return split_lines


@command_line_interface.command(
    "format-code",
    cls=APIGroup,
    help="Команда для форматирования блоков кода",
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
    help="Флаг рекурсивного поиска файлов. \n\n\bПо умолчанию: True",
    show_default=True,
    required=False,
    default=True)
@option(
    "-l", "--length",
    type=INT,
    help=f"Максимальная длина строки. \n\bПо умолчанию: {MAX_LENGTH}",
    multiple=False,
    required=False,
    metavar="<LEN>",
    default=MAX_LENGTH)
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
@pass_context
def format_code_command(
        ctx: Context,
        files: Iterable[str | Path] = None,
        directory: str | Path = None,
        recursive: bool = True,
        length: int = MAX_LENGTH):
    files: list[str | Path] | None = get_files(files, directory, recursive)

    if files is None:
        pause(PRESS_ENTER_KEY)
        ctx.exit(0)

    for file in files:
        try:
            with open(file, "r", encoding="utf-8", errors="ignore") as fr:
                _content: str = fr.read()

            _result: list[str] = []

            for code in finditer(r"`{3}\S*\n(.*?)\n`{3}", _content):
                lines: list[str] = code.group(1).splitlines()

                for line in lines:
                    _: list[str] = split(line, length=length)
                    _result.append("\n".join(_))

            with open(file, "w", encoding="utf-8", errors="ignore") as fw:
                fw.write("\n\n".join(_result))

            logger.info(f"Файл {file.name} успешно обработан")

        except PermissionError:
            logger.error(f"Недостаточно прав для чтения/записи в файл {file.name}")
            continue

        except RuntimeError:
            logger.error(f"Истекло время чтения/записи файл {file.name}")
            continue

        except OSError as e:
            logger.error(f"Ошибка {e.__class__.__name__}: {e.strerror}")
            continue

    pause(PRESS_ENTER_KEY)
    ctx.exit(0)
