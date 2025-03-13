# -*- coding: utf-8 -*-
from os import system
from pathlib import Path
from sys import platform
from typing import Iterable

from rich import print
from loguru import logger
from typer.main import Typer
from typer.models import Context
from typer.params import Option
from typing_extensions import Annotated, List

from utilities.common.constants import pretty_print, separator, StrPath
from utilities.common.functions import file_reader, ReaderMode, clear_logs
from utilities.scripts.list_files import get_files
from utilities.scripts.main_group import MainGroup

RUSSIAN_CHARS: str = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"

check_russian: Typer = Typer(
    cls=MainGroup,
    add_help_option=False,
    rich_markup_mode="rich",
    help="Команда для проверки наличия непереведенных слов")


def wrap_text(
        value: str, *,
        is_color: bool = True,
        is_success: bool = False):
    if is_color and is_success:
        prefix: str = "[green]"
        postfix: str = "[/green]"

    elif is_color and not is_success:
        prefix: str = "[red]"
        postfix: str = "[/red]"

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
             wrap_iterable(
                 results,
                 is_color=is_color,
                 is_success=False)))


@check_russian.command(
    add_help_option=False,
    name="check-russian",
    help="Команда для проверки наличия непереведенных слов")
def check_russian_command(
        ctx: Context,
        files: Annotated[
            List[Path],
            Option(
                "--file", "-f",
                help="Файл для обработки. Может использоваться несколько раз",
                metavar="FILE ... FILE",
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
        verbose: Annotated[
            bool,
            Option(
                "--verbose/--quiet", "-v/-q",
                show_default=True,
                help="Флаг подробного вывода.\nПо умолчанию: False, выводятся только ошибки")] = False,
        keep_logs: Annotated[
            bool,
            Option(
                "--keep-logs",
                show_default=True,
                help="Флаг сохранения директории с лог-файлом по завершении\nработы в штатном режиме."
                     "\nПо умолчанию: False, лог-файл и директория удаляются")] = False,
        help_option: Annotated[
            bool,
            Option(
                "-h", "--help",
                show_default=False,
                help="Показать справку и закрыть окно",
                is_eager=True)] = False):
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

        if not result and not verbose:
            final: str = wrap_text(
                "Ни в одном файле не обнаружены кириллические буквы",
                is_color=is_color,
                is_success=True)

        else:
            final: str = pretty_print(result)

        print(final)

    else:
        logger.warning("Не найдено ни одного подходящего файла")

    ctx.obj["keep_logs"] = keep_logs
    ctx.invoke(clear_logs)
