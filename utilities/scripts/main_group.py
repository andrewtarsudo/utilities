# -*- coding: utf-8 -*-
from operator import attrgetter
from sys import platform
from typing import Any, Iterable

from click.core import Argument, Command, Option, Parameter
from click.formatting import HelpFormatter
from click.globals import get_current_context
from loguru import logger
from typer.core import TyperGroup
from typer.models import Context

from utilities.common.constants import args_help_dict, HELP
from utilities.common.errors import NoArgumentsOptionsError

COL_MAX: int = 39
MAX_CONTENT_WIDTH: int = 96
TERMINAL_WIDTH: int = 96

SEPARATOR: str = "-" * MAX_CONTENT_WIDTH


def wrap_line(line: str):
    if len(line) >= MAX_CONTENT_WIDTH:
        pipe_indexes: list[int] = [index for index, char in enumerate(line) if char == "|"]
        index: int = max(filter(lambda x: x <= MAX_CONTENT_WIDTH, pipe_indexes))
        line: str = f"{line[:index + 1]}\n{wrap_line(line[index + 2:])}"

    return line


def format_usage(cmd: Command, ctx: Context, formatter: HelpFormatter) -> None:
    args: list[str] = []
    opts: list[str] = []

    for param in cmd.params:
        if param.name == "help":
            continue

        elif isinstance(param, Option):
            _opts: str = "/".join(param.opts)

            if param.hidden:
                continue

            if param.type.name != "boolean":
                _metavar: str = f" {param.make_metavar()}"

            elif param.name in ("version", "help"):
                _metavar: str = f""

            else:
                _metavar: str = ""

            _param: str = f"{_opts}{_metavar}"
            opts.append(_param)

        else:
            _param: str = f"<{param.make_metavar()}>"
            args.append(_param)

    args_str: str = " ".join(args) if args else ""
    opts_str: str = " | ".join(opts) if opts else ""
    opts_str: str = f"{opts_str} | --h/--help"

    commands: dict[str, Command] = getattr(cmd, "commands", None)
    suffix: str = "" if not platform.startswith("win") else ".exe"
    name: str = ctx.command_path.replace("__main__.py", f"tw_utilities{suffix}")

    if commands is not None and commands != dict():
        commands_str: str = wrap_line(" | ".join(map(str, commands)))
        formatter.write(
            f"Использование:\n{name}\n"
            f"{commands_str}\n{wrap_line(opts_str)}\n{wrap_line(args_str)}\n")

    else:

        formatter.write(
            f"Использование:\n{name} {args_str}\n{wrap_line(opts_str)}\n")


def format_options(cmd: Command, ctx: Context, formatter: HelpFormatter) -> None:
    def modify_help_record(parameter: Parameter):
        if isinstance(parameter, Argument):
            return None

        elif isinstance(parameter, Option) and parameter.hidden:
            return None

        option_help: str
        _, option_help = parameter.get_help_record(ctx)

        try:
            _index: int = option_help.index("[default")

        except ValueError:
            pass

        else:
            option_help: str = option_help[:_index]

        finally:
            return _, option_help

    rows: list[tuple[str, str]] = []

    for param in cmd.get_params(ctx):
        if param.name != "help":
            rv: tuple[str, str] = modify_help_record(param)

            if rv is not None:
                rows.append(rv)

        else:
            rows.append(("-h, --help", HELP))

    if rows:
        formatter.width = MAX_CONTENT_WIDTH

        with formatter.section("Опции"):
            opt_names: list[str] = [item[0] for item in rows]

            col_spacing: int = COL_MAX - max(map(len, opt_names))
            col_max: int = MAX_CONTENT_WIDTH
            formatter.write_dl(rows, col_max, col_spacing)


def format_epilog(cmd: Command, parent: Context = None, formatter: HelpFormatter = None) -> None:
    if parent is None:
        parent: Context = get_current_context()

    if formatter is None:
        formatter: HelpFormatter = parent.make_formatter()

    formatter.width = MAX_CONTENT_WIDTH

    commands: dict[str, Command] = getattr(cmd, "commands", dict())

    if commands != dict():
        with formatter.section("Подкоманды"):
            rows: list[tuple[str, str]] = [
                (sub.name, sub.help)
                for sub in sorted(commands.values(), key=attrgetter("name"))
                if not sub.hidden]

            sub_names: list[str] = [sub.name for sub in commands.values() if not sub.hidden]
            col_spacing: int = COL_MAX - max(map(len, sub_names))
            col_max: int = MAX_CONTENT_WIDTH

            formatter.write_dl(rows, col_max, col_spacing)


def format_help(cmd: Command, ctx: Context, formatter: HelpFormatter) -> None:
    format_usage(cmd, ctx, formatter)
    cmd.format_help_text(ctx, formatter)
    format_args(cmd, ctx, formatter)
    format_options(cmd, ctx, formatter)
    format_epilog(cmd, ctx, formatter)


# noinspection PyTypeChecker
def format_args(cmd: Command, ctx: Context, formatter: HelpFormatter):
    args: list[Argument] = [
        param for param in cmd.get_params(ctx)
        if isinstance(param, Argument)]

    if args:
        formatter.width = MAX_CONTENT_WIDTH

        keys: list[str] = [item.removesuffix(".exe") for item in ctx.command_path.split(" ")]
        rows: list[tuple[str, str]] = [
            (arg.name, args_help_dict.get_multiple_keys(keys=keys).get(arg.name))
            for arg in args]

        args_names: list[str] = [arg.name for arg in args]

        col_spacing: int = COL_MAX - max(map(len, args_names))
        col_max: int = MAX_CONTENT_WIDTH

        with formatter.section("Аргументы"):
            formatter.write_dl(rows, col_max, col_spacing)


def get_help(cmd: Command, ctx: Context) -> str:
    ctx.max_content_width = MAX_CONTENT_WIDTH
    ctx.terminal_width = TERMINAL_WIDTH

    formatter: HelpFormatter = ctx.make_formatter()
    format_help(cmd, ctx, formatter)
    return formatter.getvalue().rstrip("\n")


def recursive_help(cmd: Command, parent: Context = None, lines: Iterable[str] = None):
    if lines is None:
        lines: list[str] = []

    else:
        lines: list[str] = [*lines]

    ctx: Context = Context(
        cmd,
        info_name=cmd.name,
        parent=parent,
        color=True,
        terminal_width=TERMINAL_WIDTH,
        max_content_width=MAX_CONTENT_WIDTH)

    lines.append(f"{get_help(cmd, ctx)}\n{SEPARATOR}\n\n")
    commands: dict[str, Command] = getattr(cmd, "commands", dict())

    for sub in commands.values():
        if not sub.hidden:
            recursive_help(sub, ctx, lines)

    return "\n".join(lines)


class MainGroup(TyperGroup):
    def __init__(self, **attrs: Any):
        super().__init__(**attrs)
        self.add_help_option = True

    def parse_args(self, ctx: Context, args: list[str]) -> list[str]:
        if args is None or not args:
            logger.error(f"Для команды {ctx.command_path} не задано ни одного аргумента или опции")
            logger.error(f"Для вызова справки используется\n{ctx.command_path} --help")
            raise NoArgumentsOptionsError

        else:
            return super().parse_args(ctx, args)

    def format_usage(self, ctx: Context, formatter: HelpFormatter) -> None:
        format_usage(self, ctx, formatter)

    def get_usage(self, ctx: Context) -> str:
        formatter: HelpFormatter = ctx.make_formatter()
        self.format_usage(ctx, formatter)

        return formatter.getvalue().rstrip("\n")

    def format_args(self, ctx: Context, formatter: HelpFormatter):
        format_args(self, ctx, formatter)

    def format_options(self, ctx: Context, formatter: HelpFormatter) -> None:
        format_options(self, ctx, formatter)

    def format_epilog(self, ctx: Context, formatter: HelpFormatter) -> None:
        format_epilog(self, ctx, formatter)

    def format_help(self, ctx: Context, formatter: HelpFormatter) -> None:
        self.add_help_option = False
        # if self.rich_markup_mode is not None:
        self.format_usage(ctx, formatter)
        self.format_help_text(ctx, formatter)
        self.format_args(ctx, formatter)
        self.format_options(ctx, formatter)
        self.format_epilog(ctx, formatter)

        #     if hasattr(self, "commands"):
        #         formatter.write(f"{SEPARATOR}\n\n")
        #
        #         for command_name in sorted(self.commands):
        #             command: Command = self.commands.get(command_name)
        #
        #             if not command.hidden:
        #                 formatter.write(recursive_help(command, ctx))
        #
        # else:
        #     return rich_format_help(
        #         obj=self,
        #         ctx=ctx,
        #         markup_mode=self.rich_markup_mode)
