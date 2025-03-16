# -*- coding: utf-8 -*-
from click import secho as secho
from click.core import Command as Command, Context, Group, Option, Parameter as Parameter
from click.formatting import HelpFormatter as HelpFormatter
from typing import Any, Iterable, Mapping
from utilities.common.shared import DEBUG as DEBUG, HELP as HELP, NORMAL as NORMAL, \
    PRESS_ENTER_KEY as PRESS_ENTER_KEY, __version__ as __version__, args_help_dict as args_help_dict
from utilities.common.custom_logger import custom_logging as custom_logging
from utilities.common.errors import BaseError as BaseError, NoArgumentsOptionsError as NoArgumentsOptionsError

COL_MAX: int
MAX_CONTENT_WIDTH: int
TERMINAL_WIDTH: int
SEPARATOR: str


def up(value: str): ...


def underscore_to_dash(value: str, *, prefix: bool = True): ...


def wrap_line(line: str): ...


def add_brackets(value: str): ...


def format_usage(cmd: Command, ctx: Context, formatter: HelpFormatter) -> None: ...


def format_options(cmd: Command, ctx: Context, formatter: HelpFormatter) -> None: ...


def format_epilog(cmd: Command, parent: Context = None, formatter: HelpFormatter = None) -> None: ...


def format_help(cmd: Command, ctx: Context, formatter: HelpFormatter) -> None: ...


def format_args(cmd: Command, ctx: Context, formatter: HelpFormatter): ...


def get_help(cmd: Command, ctx: Context) -> str: ...


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


class SwitchArgsAPIGroup(APIGroup):
    def parse_args(self, ctx: Context, args: list[str]): ...


class TermsAPIGroup(APIGroup):
    def parse_args(self, ctx: Context, args: list[str]): ...


class MutuallyExclusiveOption(Option):
    mutually_exclusive: set[str]

    def __init__(self, *args, **kwargs) -> None: ...

    def handle_parse_result(self, ctx: Context, opts: Mapping[str, Any], args: Iterable[str]) -> tuple[
        Any, list[str]]: ...


def command_line_interface(debug: bool = False): ...


def clear_logs(ctx: Context): ...
