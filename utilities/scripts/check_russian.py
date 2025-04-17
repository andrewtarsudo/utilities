# -*- coding: utf-8 -*-
from os import system
from typing import Iterable

from click.core import Context
from click.decorators import help_option, option, pass_context
from click.termui import style
from click.types import BOOL, Path as ClickPath
from click.utils import echo
from loguru import logger

from utilities.common.functions import file_reader, is_windows, pretty_print
from utilities.common.shared import HELP, separator, StrPath
from utilities.scripts.api_group import APIGroup
from utilities.scripts.cli import clear_logs, cli
from utilities.scripts.completion import dir_completion, file_completion
from utilities.scripts.list_files import get_files

RUSSIAN_CHARS: str = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"


def style_iterable(values: Iterable[str], fg: str):
    lines: list[str] = [style(value, fg=fg) for value in values]
    return pretty_print(lines)


def find_first_russian_char(line: str):
    for index, char in enumerate(line):
        if char in RUSSIAN_CHARS:
            return index, char

    return None


def file_inspection(path: str, is_color: bool = True):
    lines: list[str] = file_reader(path, "lines", encoding="utf-8")

    results: list[str] = []

    for line_no, line in enumerate(lines):
        _: tuple[int, str] | None = find_first_russian_char(line)

        if _ is not None:
            index, char = _
            record: str = style(f"Строка {line_no + 1}, символ {index + 1}: {char}", fg="red")
            results.append(record)

    if not results and is_color:
        return style(f"В файле {path} не найдены кириллические буквы", fg="green")

    elif not results and not is_color:
        return None

    elif results and not is_color:
        return f"{separator}\nВ файле {path} найдены кириллические буквы:\n{pretty_print(results)}"

    elif results and is_color:
        return pretty_print(
            (style(f"В файле {path} найдены кириллические буквы:", fg="red"),
             style_iterable(results, fg="red")))


@cli.command(
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
    shell_complete=dir_completion,
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
    shell_complete=file_completion,
    default=None)
@option(
    "-v/-q", "--verbose/--quiet",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг подробного вывода."
         "\nПо умолчанию: False, выводятся только ошибки",
    show_default=True,
    required=False,
    default=False)
@option(
    "-r/-R", "--recursive/--no-recursive",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг рекурсивного поиска файлов."
         "\nПо умолчанию: True, вложенные файлы учитываются",
    show_default=True,
    required=False,
    default=True)
@option(
    "-k/-K", "--keep-logs/--remove-logs",
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
    if is_windows():
        system("color")

    files: list[StrPath] | None = get_files(
        ctx,
        files=files,
        directory=directory,
        recursive=recursive,
        language="en",
        extensions="md adoc")

    if files is not None and files:
        result: list[str] = []

        for file in files:
            logger.debug(f"Файл {file}")
            file_result: str | None = file_inspection(file, verbose)

            if file_result is not None:
                result.append(file_result)
                logger.debug(file_result)

        if not result and not verbose:
            final: str = style("Ни в одном файле не обнаружены кириллические буквы", fg="green")

        else:
            final: str = pretty_print(result)

        echo(final)

    else:
        logger.warning("Не найдено ни одного подходящего файла")

    ctx.obj["keep_logs"] = keep_logs
    ctx.invoke(clear_logs)
