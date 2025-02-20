# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Any, Iterable

from click.core import Context, Parameter
from click.decorators import argument, help_option, option, pass_context
from click.termui import pause
from click.types import BOOL
from click.utils import echo
from loguru import logger

from utilities.common.constants import HELP, PRESS_ENTER_KEY, pretty_print
from utilities.common.functions import file_reader, ReaderMode
from utilities.scripts import APIGroup
from utilities.scripts.cli import clear_logs, command_line_interface, MutuallyExclusiveOption
from utilities.terms.ascii_doc_table_terms import AsciiDocTableTerms
from utilities.terms.git_manager import git_manager
from utilities.terms.table import Term

_SOURCES: Path = Path(__file__).parent.parent.parent.joinpath("sources")
INFO_FILE: Path = _SOURCES.joinpath("help.txt")
README_FILE: Path = _SOURCES.joinpath("readme.txt")
SAMPLES_FILE: Path = _SOURCES.joinpath("samples.txt")


# noinspection PyUnusedLocal
def print_file(ctx: Context, param: Parameter, value: Any):
    if not value or ctx.resilient_parsing:
        return

    command_files: dict[str, Path] = {
        "info_flag": INFO_FILE,
        "readme_flag": README_FILE,
        "samples_flag": SAMPLES_FILE}

    path: Path = command_files.get(param.name)

    result: str = file_reader(path, ReaderMode.STRING)
    echo(result)
    pause(PRESS_ENTER_KEY)
    ctx.exit(0)


@command_line_interface.command(
    "terms",
    cls=APIGroup,
    help="Команда для вывода расшифровки аббревиатур")
@argument(
    "terms",
    required=False,
    metavar="TERMS",
    nargs=-1,
    default=None)
@option(
    "-a", "--all", "all_flag",
    is_flag=True,
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["full_flag", "readme_flag", "samples_flag"],
    help="\b\nФлаг вывода всех сокращений",
    show_default=True,
    required=False,
    is_eager=True,
    default=False)
@option(
    "-f", "--full", "full_flag",
    is_flag=True,
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["all_flag", "readme_flag", "samples_flag"],
    help="\b\nФлаг вывода всех сокращений с их расшифровками",
    show_default=True,
    required=False,
    is_eager=True,
    default=False)
@option(
    "-i", "--info", "info_flag",
    is_flag=True,
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["full_flag", "all_flag", "samples_flag", "readme_flag"],
    help="\b\nФлаг вывода полного руководства",
    show_default=True,
    required=False,
    is_eager=True,
    callback=print_file,
    default=False)
@option(
    "-r", "--readme", "readme_flag",
    is_flag=True,
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["full_flag", "all_flag", "samples_flag", "info_flag"],
    help="\b\nФлаг вывода полного руководства",
    show_default=True,
    required=False,
    is_eager=True,
    callback=print_file,
    default=False)
@option(
    "-s", "--samples", "samples_flag",
    is_flag=True,
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["full_flag", "readme_flag", "all_flag", "info_flag"],
    help="\b\nФлаг вывода примеров использования",
    show_default=True,
    required=False,
    is_eager=True,
    callback=print_file,
    default=False)
@option(
    "--abbr", "abbr_flag",
    is_flag=True,
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["ascii_flag", "common_flag"],
    help="\b\nФлаг вывода сокращения для добавления в файл Markdown.\nФормат: <abbr title=\"\"></abbr>",
    show_default=True,
    required=False,
    default=False)
@option(
    "--ascii", "ascii_flag",
    is_flag=True,
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["abbr_flag", "common_flag"],
    help="\b\nФлаг вывода сокращения для добавления в файл AsciiDoc.\nФормат: pass:q[<abbr title=\"\"></abbr>]",
    show_default=True,
    required=False,
    default=False)
@option(
    "--common", "common_flag",
    is_flag=True,
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["abbr_flag", "ascii_flag"],
    help="\b\nФлаг вывода сокращения в свободном виде",
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
def terms_command(
        ctx: Context,
        terms: Iterable[str] = None, *,
        all_flag: bool = False,
        full_flag: bool = False,
        info_flag: bool = False,
        readme_flag: bool = False,
        samples_flag: bool = False,
        abbr_flag: bool = False,
        ascii_flag: bool = False,
        keep_logs: bool = False,
        common_flag: bool = False):
    git_manager.set_content_git_pages()
    git_manager.compare()
    git_manager.set_terms()

    lines: list[str] = list(iter(git_manager))

    ascii_doc_table: AsciiDocTableTerms = AsciiDocTableTerms(lines)
    ascii_doc_table.complete()
    ascii_doc_table.set_terms()

    if all_flag:
        result: str = file_reader(INFO_FILE, ReaderMode.STRING)

    elif full_flag:
        terms_full: list[Term] = [v for values in iter(ascii_doc_table.dict_terms.values()) for v in values]
        result: str = "\n".join(map(lambda x: x.formatted(), terms_full))

    elif info_flag:
        result: str = file_reader(INFO_FILE, ReaderMode.STRING)

    elif readme_flag:
        result: str = file_reader(README_FILE, ReaderMode.STRING)

    elif samples_flag:
        result: str = file_reader(SAMPLES_FILE, ReaderMode.STRING)

    elif terms is None or not terms:
        echo("Не задана ни одна аббревиатура")
        result: str = ""

    else:
        terms_print: list[Term] = []

        if isinstance(terms, str):
            terms: list[str] = [terms]

        for term in terms:
            term: str = term.upper()

            if term not in ascii_doc_table.terms_short():
                terms_print.append(Term())

            else:
                terms_print.extend(ascii_doc_table.get(term))

        if abbr_flag:
            result: str = pretty_print(map(lambda x: x.abbr(), terms_print))

        elif ascii_flag:
            result: str = pretty_print(map(lambda x: x.adoc(), terms_print))

        elif common_flag:
            result: str = pretty_print(map(lambda x: x.formatted(), terms_print))

        else:
            result: str = pretty_print(map(lambda x: x.formatted(), terms_print))

    logger.success(result)

    ctx.obj["keep_logs"] = keep_logs
    ctx.invoke(clear_logs)
