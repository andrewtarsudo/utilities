# -*- coding: utf-8 -*-
from re import finditer, Match
from typing import Iterable

from click.core import Context
from click.decorators import help_option, option, pass_context
from click.types import BOOL, INT, Path as ClickPath
from loguru import logger

from utilities.common.config import config_file
from utilities.common.errors import FormatCodeNonIntegerLineLengthError, FormatCodeNonPositiveLineLengthError
from utilities.common.functions import file_reader, file_writer, pretty_print
from utilities.common.shared import ADOC_EXTENSION, HELP, MD_EXTENSION, StrPath
from utilities.scripts.api_group import APIGroup
from utilities.scripts.cli import cli
from utilities.scripts.completion import dir_completion, file_completion
from utilities.scripts.list_files import get_files

MAX_LENGTH: int = config_file.get_commands("format-code", "length")


@cli.command(
    "format-code",
    cls=APIGroup,
    help="Команда для форматирования блоков кода")
@option(
    "-f", "--file", "files",
    type=ClickPath(
        file_okay=True,
        readable=True,
        resolve_path=True,
        allow_dash=False,
        dir_okay=False),
    help="\b\nФайлы для обработки. Может использоваться несколько раз",
    multiple=True,
    required=False,
    metavar="FILE ... FILE",
    shell_complete=file_completion,
    default=config_file.get_commands("format-code", "files"))
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
    shell_complete=dir_completion,
    default=config_file.get_commands("format-code", "directory"))
@option(
    "-l", "--length",
    type=INT,
    help=f"\b\nМаксимальная длина строки. По умолчанию: {MAX_LENGTH}"
         f"\nПримечание. Должно быть целым положительным числом",
    multiple=False,
    required=False,
    metavar="LEN",
    default=config_file.get_commands("format-code", "length"))
@option(
    "-r/-R", "--recursive/--no-recursive",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг рекурсивного поиска файлов."
         "\nПо умолчанию: True, вложенные файлы учитываются",
    show_default=True,
    required=False,
    default=config_file.get_commands("format-code", "recursive"))
@option(
    "-k/-K", "--keep-logs/--remove-logs",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг сохранения директории с лог-файлом по завершении"
         "\nработы в штатном режиме."
         "\nПо умолчанию: False, лог-файл и директория удаляются",
    show_default=True,
    required=False,
    default=config_file.get_commands("format-code", "keep_logs"))
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
@pass_context
def format_code_command(
        ctx: Context,
        directory: StrPath = None,
        files: Iterable[StrPath] = None,
        recursive: bool = True,
        length: int = MAX_LENGTH,
        keep_logs: bool = False):
    if length < 0:
        logger.error(f"Максимальная длина не может быть неположительным числом, однако получено {length}")
        raise FormatCodeNonPositiveLineLengthError

    elif not isinstance(length, int):
        logger.error(f"Максимальная длина должна быть целым числом, однако получено {type(length).__name__}")
        raise FormatCodeNonIntegerLineLengthError

    files: list[StrPath] | None = get_files(
        ctx,
        files=files,
        directory=directory,
        recursive=recursive,
        language=None)

    patterns: dict[str, str] = {
        MD_EXTENSION: r"```\S*\n(.*?)\n```",
        ADOC_EXTENSION: r"(?:-{4}|={4}|\.{4})([\s\S]+)(?:-{4}|={4}|\.{4})"}

    if files is not None and files:
        for file in files:
            logger.debug(f"Файл {file}")

            try:
                _content: str = file_reader(file, "string")

                _result: list[str] = []

                for code in finditer(patterns.get(file.suffix), _content):
                    lines: list[str] = code.group(1).splitlines()

                    for line in lines:
                        _: list[str] = split(line, length=length)
                        _result.append(pretty_print(_))

                file_writer(file, pretty_print(_result))

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

    ctx.obj["keep_logs"] = keep_logs


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
                stop_square_bracket: int = _slice.rfind("[")
                stop_curly_bracket: int = _slice.rfind("(")
                stop_comma: int = _slice.rfind(",")

                stop: int = max(stop_square_bracket, stop_curly_bracket, stop_comma)

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
