# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Annotated, Any

from click.core import Context, Parameter
from click.exceptions import Exit
from click.termui import pause
from click.utils import echo
from loguru import logger
from typer.main import Typer
from typer.params import Argument, Option
from typing_extensions import List

from utilities.common.constants import PRESS_ENTER_KEY, pretty_print
from utilities.common.functions import clear_logs, file_reader, ReaderMode
from utilities.terms.ascii_doc_table_terms import AsciiDocTableTerms
from utilities.terms.git_manager import git_manager
from utilities.terms.table import Term

_SOURCES: Path = Path(__file__).parent.parent.parent.joinpath("sources")
INFO_FILE: Path = _SOURCES.joinpath("help.txt")
README_FILE: Path = _SOURCES.joinpath("readme.txt")
SAMPLES_FILE: Path = _SOURCES.joinpath("samples.txt")

terms: Typer = Typer(
    add_help_option=True,
    rich_markup_mode="rich",
    help="Команда для вывода расшифровки аббревиатур")


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
    Exit(0)


@terms.command(
    name="terms",
    help="Команда для вывода расшифровки аббревиатур")
def terms_command(
        ctx: Context,
        acronyms: Annotated[
            List[str],
            Argument(
                metavar="TERM .. TERM",
                help="Перечень запрашиваемых аббревиатур")] = None, *,
        all_flag: Annotated[
            bool,
            Option(
                "-a", "--all",
                show_default=True,
                help="Флаг вывода всех сокращений")] = False,
        full_flag: Annotated[
            bool,
            Option(
                "-f", "--full",
                show_default=True,
                help="Флаг вывода всех сокращений с их расшифровками")] = False,
        info_flag: Annotated[
            bool,
            Option(
                "-i", "--info",
                show_default=True,
                help="Флаг вывода полного руководства")] = False,
        readme_flag: Annotated[
            bool,
            Option(
                "-r", "--readme",
                show_default=True,
                help="Флаг вывода полного руководства")] = False,
        samples_flag: Annotated[
            bool,
            Option(
                "-s", "--samples",
                show_default=True,
                help="Флаг вывода примеров использования")] = False,
        abbr_flag: Annotated[
            bool,
            Option(
                "--abbr",
                show_default=True,
                help="Флаг вывода сокращения для добавления в файл Markdown."
                     "\nФормат: <abbr title=\"\"></abbr>")] = False,
        ascii_flag: Annotated[
            bool,
            Option(
                "--ascii",
                show_default=True,
                help="Флаг вывода сокращения для добавления в файл AsciiDoc."
                     "\nФормат: pass:q[<abbr title=\"\"></abbr>]")] = False,
        keep_logs: Annotated[
            bool,
            Option(
                "--keep-logs",
                show_default=True,
                help="Флаг сохранения директории с лог-файлом по завершении\nработы в штатном режиме."
                     "\nПо умолчанию: False, лог-файл и директория удаляются")] = False,
        common_flag: Annotated[
            bool,
            Option(
                "--common",
                show_default=True,
                help="Флаг вывода сокращения в свободном виде")] = False):
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

    elif acronyms is None or not acronyms:
        echo("Не задана ни одна аббревиатура")
        result: str = ""

    else:
        terms_print: list[Term] = []

        if isinstance(acronyms, str):
            acronyms: list[str] = [acronyms]

        for term in acronyms:
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
