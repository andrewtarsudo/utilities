# -*- coding: utf-8 -*-
from pathlib import Path
from re import sub
from typing import Iterable

from click.core import Context
from click.decorators import option, pass_context
from click.types import BOOL
from loguru import logger

from scripts.cli import APIGroup, command_line_interface
from terms.ascii_doc_table_terms import AsciiDocTableTerms
from terms.const import _interceptors, separator, State, StrNone
from terms.table import _Term

_SOURCES: Path = Path(__file__).parent.joinpath("sources")
HELP_FILE: Path = _SOURCES.joinpath("help.txt")
README_FILE: Path = _SOURCES.joinpath("readme.txt")
SAMPLES_FILE: Path = _SOURCES.joinpath("samples.txt")


def _print_dictionary(terms: Iterable[_Term]) -> str:
    return "\n".join(list(map(lambda x: x.formatted(), terms)))


def _print_help() -> str:
    with open(HELP_FILE, "rb+") as help_doc:
        help_text: bytes = help_doc.read()

    return help_text.decode(encoding="utf8")


def _print_short(table_terms: AsciiDocTableTerms) -> str:
    return ", ".join(table_terms.terms_short())


def _print_readme() -> str:
    with open(README_FILE, "rb+") as readme_doc:
        readme_text: bytes = readme_doc.read()

    return readme_text.decode(encoding="utf8")


def _print_samples() -> str:
    with open(SAMPLES_FILE, "rb+") as samples_doc:
        samples_text: bytes = samples_doc.read()

    return samples_text.decode(encoding="utf8")


class LineParser:
    _separators: str = r"['!$@<> .,;:*|\/+#{}=]"

    def __init__(self, line: str):
        self._line: str = line.strip()

    def __str__(self):
        return f"{self._line}"

    def __repr__(self):
        return f"<{self.__class__.__name__}({self._line})>"

    @property
    def line(self) -> str:
        return self._line

    @line.setter
    def line(self, value):
        self._line = value

    @property
    def up(self) -> str:
        return self._line.upper()

    @property
    def down(self) -> str:
        return self._line.lower()

    def parse_user_input(self, line: StrNone = None) -> list[str]:
        if line is None:
            line: str = self.up

        return self.multi_split(line)

    def check_line_start(self, line: StrNone = None, *, start: Iterable[str] = None):
        if start is None:
            return False

        if line is None:
            line: str = self.down

        return any(line.startswith(_item) for _item in start)

    def multi_split(self, line: StrNone = None, *, separators: StrNone = None):
        if line is None:
            line: str = self.down

        if separators is None:
            separators: str = self._separators

        _line: str = sub(separators, "\t", line)

        return _line.split("\t")


class UserInputParser:
    def __init__(self, table_terms: AsciiDocTableTerms):
        self._table_terms: AsciiDocTableTerms = table_terms
        self.state: State = State.ACTIVE
        self._input: StrNone = None

    def __repr__(self):
        return f"<{self.__class__.__name__}({self._table_terms.__name__})>"

    def __str__(self):
        return f"{self.__class__.__name__}\n{self._table_terms.terms_short()}"

    def line_parser(self):
        if self._input is not None:
            return LineParser(self._input)

    @property
    def _actions(self) -> dict[str, str]:
        _specified_actions: dict[tuple[str, str], str] = {
            ("-f", "--full"): self._print_dictionary(),
            ("-a", "--all"): self._print_short(),
            ("-r", "--readme"): _print_readme(),
            ("-s", "--samples"): _print_samples(),
            ("-h", "--help"): _print_help()
        }

        return {_action: value for key, value in _specified_actions.items() for _action in key}

    def _print_dictionary(self) -> str:
        return "\n".join(list(map(lambda x: x.formatted(), self._terms())))

    def _print_short(self) -> str:
        return ", ".join(self._table_terms.terms_short())

    def handle_input(self, user_input: str = None):
        if not user_input or user_input is None:
            return

        logger.debug(f"User input = {user_input}")
        self._input: str = user_input

        if self.line_parser().check_line_start(start=_interceptors):
            logger.info("Программа остановлена пользователем")
            self.state = State.STOPPED
            return

        _lower: str = self.line_parser().down

        if self.line_parser().check_line_start(_lower, start=self._actions):
            _: str = self._actions.get(_lower)

        else:
            _: str = self._handle_user_terms()

        results: str = "".join(("\n", _, "\n", separator))
        logger.info(f"{results}")
        return

    def _terms(self) -> list[_Term]:
        return [v for values in iter(self) for v in values]

    def _handle_user_terms(self) -> str:
        _upper: str = self.line_parser().up
        _lower: str = self.line_parser().down

        if _lower.startswith("--abbr"):
            logger.debug("--abbr mode is called")
            _to_find: list[str] = self.line_parser().parse_user_input(_upper[7:])
            _: list[str] = [term.abbr() for term in self._search_terms(_to_find)]

        elif _lower.startswith("--adoc"):
            logger.debug("--adoc mode is called")
            _to_find: list[str] = self.line_parser().parse_user_input(_upper[8:])
            _: list[str] = [term.adoc() for term in self._search_terms(_to_find)]

        else:
            logger.debug("common mode is called")
            _to_find: list[str] = self.line_parser().parse_user_input(_upper)
            _: list[str] = [term.formatted() for term in self._search_terms(_to_find)]

        return "\n".join(_)

    def _search_terms(self, terms_find: Iterable[str]) -> tuple[_Term, ...]:
        results: list[_Term] = []

        for term in terms_find:
            if term not in self._table_terms.terms_short():
                results.append(_Term())

            else:
                results.extend(self._table_terms[term])

        return *results,

    def __iter__(self):
        return iter(self._table_terms.dict_terms.values())


@command_line_interface.command(
    "terms",
    cls=APIGroup,
    help="Команда для проверки наличия непереведенных слов",
    invoke_without_command=True
)
@option(
    "-a/--all",
    type=BOOL,
    help="Флаг вывода всех сокращений",
    show_default=True,
    required=False,
    is_eager=True,
    default=False)
@option(
    "-f/--full",
    type=BOOL,
    help="Флаг вывода всех сокращений с их расшифровками",
    show_default=True,
    required=False,
    is_eager=True,
    default=False)
@option(
    "-r/--readme",
    type=BOOL,
    help="Флаг вывода полного руководства",
    show_default=True,
    required=False,
    is_eager=True,
    default=False)
@option(
    "-s/--samples",
    type=BOOL,
    help="Флаг вывода примеров использования",
    show_default=True,
    required=False,
    is_eager=True,
    default=False)
@option(
    "--abbr",
    type=BOOL,
    help="Флаг вывода сокращения для добавления в файл Markdown.\nПо умолчанию: False",
    show_default=True,
    required=False,
    default=False)
@option(
    "--ascii",
    type=BOOL,
    help="Флаг вывода сокращения для добавления в файл AsciiDoc.\nФормат: pass:q[<abbr title=""></abbr>]",
    show_default=True,
    required=False,
    default=False)
@pass_context
def terms_command(
        ctx: Context,
        all_: bool = False,
        full_: bool = False,
        readme_: bool = False,
        samples_: bool = False,
        abbr_: bool = False,
        ascii_: bool = False):
    pass
