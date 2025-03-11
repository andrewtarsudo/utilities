# -*- coding: utf-8 -*-
from pathlib import Path
from re import finditer, Match
from typing import Iterable

from click.core import Context
from loguru import logger
from typer.main import Typer
from typer.params import Option
from typing_extensions import Annotated, List

from utilities.common.constants import ADOC_EXTENSION, MD_EXTENSION, pretty_print, StrPath
from utilities.common.errors import FormatCodeNonIntegerLineLengthError, FormatCodeNonPositiveLineLengthError
from utilities.common.functions import file_reader, file_writer, ReaderMode
from utilities.scripts.cli import clear_logs
from utilities.scripts.list_files import get_files

MAX_LENGTH: int = 84

format_code: Typer = Typer()


@format_code.command(
    name="format-code",
    help="Команда для форматирования блоков кода"
)
def format_code_command(
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
        length: Annotated[
            int,
            Option(
                "-l", "--length",
                metavar="WIDTH",
                help=f"Максимальная длина строки. По умолчанию: {MAX_LENGTH}"
                     f"\nПримечание. Должно быть целым положительным числом",
                show_default=True)] = MAX_LENGTH,
        recursive: Annotated[
            bool,
            Option(
                "--recursive/--no-recursive", "-r/-R",
                show_default=True,
                help="Флаг рекурсивного поиска файлов.\nПо умолчанию: True, вложенные файлы учитываются")] = True,
        keep_logs: Annotated[
            bool,
            Option(
                "--keep-logs",
                show_default=True,
                help="Флаг сохранения директории с лог-файлом по завершении\nработы в штатном режиме."
                     "\nПо умолчанию: False, лог-файл и директория удаляются")] = False):
    if length < 0:
        logger.error(f"Максимальная длина не может быть неположительным числом, однако получено {length}")
        raise FormatCodeNonPositiveLineLengthError

    elif not isinstance(length, int):
        logger.error(f"Максимальная длина должна быть целым числом, однако получено {type(length)}")
        raise FormatCodeNonIntegerLineLengthError

    files: list[StrPath] | None = get_files(
        ctx,
        files=files,
        directory=directory,
        recursive=recursive,
        language=None)

    patterns: dict[str, str] = {
        MD_EXTENSION: r"```\S*\n(.*?)\n```",
        ADOC_EXTENSION: r"(?:-{4}|={4}|\.{4})([\s\S]+)(?:-{4}|={4}|\.{4})"
    }

    if files is not None and files:
        for file in files:
            logger.debug(f"Файл {file}")

            try:
                _content: str = file_reader(file, ReaderMode.STRING)

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
    ctx.invoke(clear_logs)


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
