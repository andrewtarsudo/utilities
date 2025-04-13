# -*- coding: utf-8 -*-
from typing import Any, Iterable, Mapping

from click.core import Command, Context, Group, Option, Parameter
from click.formatting import HelpFormatter
from click.shell_completion import CompletionItem

COL_MAX: int
MAX_CONTENT_WIDTH: int
TERMINAL_WIDTH: int
SEPARATOR: str


def up(value: str): ...


def prepare_option(value: str, *, prefix: bool = True, remove_suffix: str | None = '-flag'): ...


def wrap_line(line: str): ...


def add_brackets(value: str): ...


def format_usage(cmd: Command, ctx: Context, formatter: HelpFormatter) -> None: ...


def format_options(cmd: Command, ctx: Context, formatter: HelpFormatter) -> None: ...


def format_epilog(cmd: Command, parent: Context = None, formatter: HelpFormatter = None) -> None: ...


def format_help(cmd: Command, ctx: Context, formatter: HelpFormatter) -> None: ...


def format_full_help(cmd: Command, ctx: Context, formatter: HelpFormatter) -> None: ...


def format_args(cmd: Command, ctx: Context, formatter: HelpFormatter): ...


def get_help(cmd: Command, ctx: Context) -> str: ...


def get_full_help(cmd: Command, ctx: Context) -> str: ...


def recursive_help(cmd: Command, parent: Context = None, lines: Iterable[str] = None): ...


def print_version(ctx: Context, param: Parameter, value: Any): ...


class APIGroup(Group):
    def __init__(self, **attrs: Any) -> None: ...

    def format_help(self, ctx: Context, formatter: HelpFormatter) -> None: ...

    def format_usage(self, ctx: Context, formatter: HelpFormatter) -> None: ...

    def get_usage(self, ctx: Context) -> str: ...

    def format_options(self, ctx: Context, formatter: HelpFormatter) -> None: ...

    def format_epilog(self, ctx: Context, formatter: HelpFormatter) -> None: ...

    def format_args(self, ctx: Context, formatter: HelpFormatter): ...

    def parse_args(self, ctx: Context, args: list[str]) -> list[str]: ...

    def invoke(self, ctx: Context) -> Any: ...

    def shell_complete(self, ctx: Context, incomplete: str) -> list[CompletionItem]: ...


class SwitchArgsAPIGroup(APIGroup):
    def parse_args(self, ctx: Context, args: list[str]) -> list[str]: ...


class TermsAPIGroup(APIGroup):
    def parse_args(self, ctx: Context, args: list[str]) -> list[str]: ...


class NoArgsAPIGroup(APIGroup):
    def parse_args(self, ctx: Context, args: list[str]) -> list[str]: ...


class MutuallyExclusiveOption(Option):
    mutually_exclusive: tuple[str, ...]

    def __init__(self, *args, **kwargs) -> None: ...

    def handle_parse_result(
            self,
            ctx: Context,
            opts: Mapping[str, Any],
            args: Iterable[str]) -> tuple[Any, list[str]]: ...
