# -*- coding: utf-8 -*-
from os import system
from sys import platform
from typing import Iterable

from click import echo
from click.core import Context
from click.decorators import help_option, option, pass_context
from click.types import BOOL, Path as ClickPath
from loguru import logger

from utilities.common.constants import FAIL_COLOR, HELP, NORMAL_COLOR, PASS_COLOR, pretty_print, separator, StrPath
from utilities.common.functions import file_reader, get_files, ReaderMode
from utilities.scripts import APIGroup
from utilities.scripts.cli import clear_logs, command_line_interface

RUSSIAN_CHARS: str = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"


def wrap_text(
        value: str, *,
        is_color: bool = True,
        is_success: bool = False):
    if is_color and is_success:
        prefix: str = PASS_COLOR
        postfix: str = NORMAL_COLOR

    elif is_color and not is_success:
        prefix: str = FAIL_COLOR
        postfix: str = NORMAL_COLOR

    else:
        prefix: str = ""
        postfix: str = ""

    return f"{prefix}{value.strip()}{postfix}"


def wrap_iterable(
        values: Iterable[str], *,
        is_color: bool = True,
        is_success: bool = False):
    lines: list[str] = [wrap_text(value, is_color=is_color, is_success=is_success) for value in values]
    return pretty_print(lines)


def find_first_russian_char(line: str):
    for index, char in enumerate(line):
        if char in RUSSIAN_CHARS:
            return index, char

    else:
        return None


def file_inspection(path: str, is_color: bool = True):
    lines: list[str] = file_reader(path, ReaderMode.LINES, encoding="utf-8")

    results: list[str] = []

    for line_no, line in enumerate(lines):
        _: tuple[int, str] | None = find_first_russian_char(line)

        if _ is not None:
            index, char = _
            record: str = wrap_text(
                f"Строка {line_no + 1}, символ {index + 1}: {char}",
                is_color=is_color,
                is_success=False)
            results.append(record)

    if not results and is_color:
        return wrap_text(
            f"В файле {path} не найдены кириллические буквы",
            is_color=is_color,
            is_success=True)

    elif not results and not is_color:
        return None

    elif results and not is_color:
        return f"{separator}\nВ файле {path} найдены кириллические буквы:\n{pretty_print(results)}"

    elif results and is_color:
        return pretty_print(
            (wrap_text(f"В файле {path} найдены кириллические буквы:", is_color=is_color, is_success=False),
             wrap_iterable(results, is_color=is_color, is_success=False)))


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
    help="\b\nФайл для обработки. Может использоваться несколько раз",
    multiple=True,
    required=False,
    metavar="FILE ... FILE",
    default=None)
@option(
    "--verbose/--no-verbose",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг подробного вывода."
         "\nПо умолчанию: False, выводятся только ошибки",
    show_default=True,
    required=False,
    default=False)
@option(
    "--recursive/--no-recursive",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг рекурсивного поиска файлов."
         "\nПо умолчанию: True, вложенные файлы учитываются",
    show_default=True,
    required=False,
    default=True)
@option(
    "--keep-logs",
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
        language="en",
        extensions="md adoc")

    if files is not None and files:
        is_color: bool = verbose

        result: list[str] = []

        for file in files:
            logger.debug(f"Файл {file}")
            file_result: str | None = file_inspection(file, verbose)

            if file_result is not None:
                result.append(file_result)
                logger.debug(file_result)

            # with open(file, "r", encoding="utf-8", errors="ignore") as f:
            #     for index, line in enumerate(f.readlines()):
            #         _lines: list[str] = []
            #
            #         for idx, char in enumerate(line):
            #             if char in RUSSIAN_CHARS:
            #                 _first_rus_idx: int = idx + 1
            #                 _first_rus_char: str = char
            #                 _lines.append(f"Строка {index}, символ {_first_rus_idx}: {_first_rus_char}")
            #                 break
            # _info.append(pretty_print(_lines))
            # _info = [
            #     f"{index + 1}[{idx}]" for index, line in enumerate(f.readlines()) for idx, c in enumerate(line)
            #     if any(char in line for char in RUSSIAN_CHARS)]

        # if not _info and verbose:
        #     result.append(
        #         wrap_text(f"В файле {file} не найдены кириллические буквы", is_color=is_color, is_success=True))
        #
        # elif not _info and not verbose:
        #     continue
        #
        # else:
        #     _: str = ', '.join(_info)
        #     wrapped: str = wrap_text(_, is_color=is_color, is_success=False)
        #     end: str = verbose * f"\n{separator}"
        #     result.append(
        #         f"{separator}\nВ файле {file} найдены кириллические буквы в строках:\n{wrapped}{end}")

        if not result and not verbose:
            final: str = wrap_text(
                "Ни в одном файле не обнаружены кириллические буквы",
                is_color=is_color,
                is_success=True)

        else:
            final: str = pretty_print(result)

        echo(final)

    else:
        logger.warning("Не найдено ни одного подходящего файла")

    ctx.obj["keep_logs"] = keep_logs
    ctx.invoke(clear_logs)
