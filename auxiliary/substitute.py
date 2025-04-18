# -*- coding: utf-8 -*-
from json import dumps
from re import Match, sub
from typing import Iterable

from click.core import Context
from click.decorators import help_option, option, pass_context
from click.types import BOOL, Path as ClickPath
from loguru import logger

from utilities.common.functions import file_reader, file_writer
from utilities.common.shared import HELP, StrPath
from utilities.scripts.cli import APIGroup, cli
from utilities.scripts.list_files import get_files


def substitute(file: StrPath, dry_run: bool = False):
    translation_table: dict[str, str] = {
        "{global_title}": 'pass:q[<abbr title="Global Title">GT</abbr>]',
        "{np}": 'pass:q[<abbr title="Numbering Plan">NP</abbr>]',
        "{ssn}": 'pass:q[<abbr title="Subsystem Number">SSN</abbr>]',
        "{tt}": 'pass:q[<abbr title="Translation Type">TT</abbr>]',
        "{nai}": 'pass:q[<abbr title="Nature of Address Indicator">NAI</abbr>]',
        "{es}": 'pass:q[<abbr title="Encoding Scheme">ES</abbr>]',
        "{acn}": 'pass:q[<abbr title="Application Context Name">ACN</abbr>]',
        "{npi}": 'pass:q[<abbr title="Numbering Plan Indicator">NPI</abbr>]',
        "{ton}": 'pass:q[<abbr title="Type of Numbering">TON</abbr>]',
        "{apn}": 'pass:q[<abbr title="Access Point Name">APN</abbr>]',
        "{rat}": 'pass:q[<abbr title="Radio Access Technology">RAT</abbr>]',
        "{msu}": 'pass:q[<abbr title="Message Signal Unit">MSU</abbr>]',
        "{pc}": 'pass:q[<abbr title="Protocol Class">PC</abbr>]',
        "{lsl}": 'pass:q[<abbr title="Low Speed Link">LSL</abbr>]',
        "{hsl}": 'pass:q[<abbr title="High Speed Link">HSL</abbr>]',
        "{spacex1}": "&nbsp;&nbsp; ",
        "{spacex2}": "&nbsp;&nbsp;&nbsp;&nbsp; ",
        "{level-1}": "&nbsp;&nbsp; ",
        "{level-2}": "&nbsp;&nbsp;&nbsp;&nbsp; ",
        "{level-3}": "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; "
    }

    logger.debug(f"Таблица замен:\n{dumps(translation_table, ensure_ascii=False, indent=2, sort_keys=False)}")
    logger.info(f"Обработка файла {file}:")

    lines: list[str] = file_reader(file, "lines")

    def repl(m: Match):
        if m.group(1) in translation_table:
            substitution: str = translation_table.get(m.group(1))
            logger.info(f"Замена {m.group(1)} -> {substitution}")
            return substitution

        else:
            logger.debug(f"{m.group(1)} нет в таблице замен")
            return m.group(1)

    lines: list[str] = [sub(r"(\{.*?})", repl, line) for line in iter(lines)]

    if not dry_run:
        file_writer(file, lines)

        logger.info(f"Обработка файла {file} завершена\n")

    else:
        logger.info(f"Все замены в файле {file} выполнены\n")


@cli.command(
    "sub-var",
    cls=APIGroup,
    help="Команда для замены переменных на их значения")
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
    default=None)
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
    default=None)
@option(
    "--dry-run/--no-dry-run",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг вывода изменений размеров файлов без их изменения.\n"
         "По умолчанию: False, файлы перезаписываются",
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
def substitute_command(
        ctx: Context,
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

    if files is not None and files:
        for file in iter(files):
            substitute(file, dry_run)

    ctx.obj["keep_logs"] = keep_logs
