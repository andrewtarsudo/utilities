# -*- coding: utf-8 -*-
from gc import collect
from operator import attrgetter
from pathlib import Path
from shutil import rmtree
from sys import platform
from typing import Any, Iterable, Mapping

from click.core import Argument, Command, Context, Group, Option, Parameter
from click.decorators import group, help_option, option, pass_context
from click.exceptions import UsageError
from click.formatting import HelpFormatter
from click.globals import get_current_context
from click.termui import pause, style
from click.types import BOOL
from click.utils import echo
from loguru import logger

from utilities.common.custom_logger import custom_logging
from utilities.common.errors import BaseError, NoArgumentsOptionsError
from utilities.common.shared import (
    __version__,
    args_help_dict,
    DEBUG,
    HELP,
    NORMAL,
    PRESS_ENTER_KEY,
    pretty_print,
)

COL_MAX: int = 52
MAX_CONTENT_WIDTH: int = 96
TERMINAL_WIDTH: int = 96

SEPARATOR: str = "-" * MAX_CONTENT_WIDTH


def up(value: str):
    return value.upper() if not value.startswith("--") else value


def prepare_option(
    value: str, *, prefix: bool = True, remove_suffix: str | None = "-flag"
):
    value: str = value.replace("_", "-")

    if remove_suffix is not None:
        value: str = value.removesuffix(remove_suffix)

    return style(f'{int(prefix) * "--"}{value}', fg="magenta", bold=True)


def wrap_line(line: str):
    if len(line) >= MAX_CONTENT_WIDTH:
        pipe_indexes: list[int] = [
            index for index, char in enumerate(line) if char == "|"
        ]
        index: int = max(filter(lambda x: x <= MAX_CONTENT_WIDTH, pipe_indexes))
        line: str = f"{line[:index + 1]}\n{wrap_line(line[index + 2:])}"

    return line


def add_brackets(value: str):
    return f"<{value}>"


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
                _metavar: str = ""

            else:
                _metavar: str = ""

            _param: str = f"{_opts}{_metavar}"
            opts.append(_param)

        else:
            _param: str = f"<{param.make_metavar()}>"
            args.append(_param)

    args_str: str = " ".join(args) if args else ""
    opts_str: str = " | ".join(opts) if opts else ""

    if cmd.name != "help":
        opts_str: str = f"{opts_str} | --h/--help"

    commands: dict[str, Command] = getattr(cmd, "commands", None)
    suffix: str = "" if not platform.startswith("win") else ".exe"
    name: str = ctx.command_path.replace("__main__.py", f"tw_utilities{suffix}")

    if commands is not None and commands != dict():
        commands_str: str = wrap_line(" | ".join(map(add_brackets, commands)))
        formatter.write(
            f"{style('Использование', fg='bright_cyan', bold=True)}:"
            f"\n{name}"
            f"\n{commands_str}"
            f"\n{wrap_line(opts_str)}"
            f"\n{wrap_line(args_str)}\n"
        )

    elif cmd.name != "help":
        formatter.write(
            f"{style('Использование', fg='bright_cyan', bold=True)}:"
            f"\n{name} {args_str}"
            f"\n{wrap_line(opts_str)}\n"
        )

    else:
        formatter.write(
            f"{style('Использование', fg='bright_cyan', bold=True)}:" f"\n{name}\n"
        )


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
            return style(_, fg="cyan", bold=True), option_help

    rows: list[tuple[str, str]] = []

    for param in cmd.get_params(ctx):
        if param.name != "help":
            rv: tuple[str, str] = modify_help_record(param)

            if rv is not None:
                rows.append(rv)

        else:
            rows.append((style("-h, --help", fg="cyan", bold=True), HELP))

    if rows:
        formatter.width = MAX_CONTENT_WIDTH

        with formatter.section(style("Опции", fg="blue", bold=True)):
            opt_names: list[str] = [item[0] for item in rows]

            col_spacing: int = COL_MAX - max(map(len, opt_names))
            col_max: int = MAX_CONTENT_WIDTH
            formatter.write_dl(rows, col_max, col_spacing)


def format_epilog(
    cmd: Command, parent: Context = None, formatter: HelpFormatter = None
) -> None:
    if parent is None:
        parent: Context = get_current_context()

    if formatter is None:
        formatter: HelpFormatter = parent.make_formatter()

    formatter.width = MAX_CONTENT_WIDTH

    commands: dict[str, Command] = getattr(cmd, "commands", dict())

    if commands != dict():
        with formatter.section(style("Подкоманды", fg="green", bold=True)):
            rows: list[tuple[str, str]] = [
                (
                    style(sub.name, fg="green", bold=True),
                    style(sub.help, fg="green", bold=True),
                )
                for sub in sorted(commands.values(), key=attrgetter("name"))
                if not sub.hidden
            ]

            sub_names: list[str] = [
                sub.name for sub in commands.values() if not sub.hidden
            ]
            col_spacing: int = COL_MAX - 2 * max(map(len, sub_names)) + 1
            col_max: int = MAX_CONTENT_WIDTH

            formatter.write_dl(rows, col_max, col_spacing)


def format_help(cmd: Command, ctx: Context, formatter: HelpFormatter) -> None:
    format_usage(cmd, ctx, formatter)
    cmd.format_help_text(ctx, formatter)
    format_args(cmd, ctx, formatter)
    format_options(cmd, ctx, formatter)
    format_epilog(cmd, ctx, formatter)


def format_full_help(cmd: Command, ctx: Context, formatter: HelpFormatter) -> None:
    format_usage(cmd, ctx, formatter)
    cmd.format_help_text(ctx, formatter)
    format_args(cmd, ctx, formatter)
    format_options(cmd, ctx, formatter)
    format_epilog(cmd, ctx, formatter)

    if hasattr(cmd, "commands") and hasattr(ctx, "obj"):
        formatter.write(f"{SEPARATOR}\n\n")

        for command_name in sorted(cmd.commands):
            command: Command = cmd.commands.get(command_name)

            if not command.hidden:
                formatter.write(recursive_help(command, ctx))


# noinspection PyTypeChecker
def format_args(cmd: Command, ctx: Context, formatter: HelpFormatter):
    args: list[Argument] = [
        param for param in cmd.get_params(ctx) if isinstance(param, Argument)
    ]

    if args:
        formatter.width = MAX_CONTENT_WIDTH
        asterisk: str = style("(*)", fg="red", bold=True)

        keys: list[str] = [
            item.removesuffix(".exe") for item in ctx.command_path.split(" ")
        ]
        rows: list[tuple[str, str]] = [
            (
                f"{style(arg.name, fg='cyan', bold=True)} {asterisk}",
                args_help_dict.get_multiple_keys(keys=keys).get(arg.name),
            )
            for arg in args
        ]

        args_names: list[str] = [arg.name for arg in args]

        col_spacing: int = COL_MAX - args_help_dict.max_key - max(map(len, args_names))
        col_max: int = MAX_CONTENT_WIDTH

        with formatter.section(style("Аргументы", fg="blue", bold=True)):
            formatter.write_dl(rows, col_max, col_spacing)


def get_help(cmd: Command, ctx: Context) -> str:
    ctx.max_content_width = MAX_CONTENT_WIDTH
    ctx.terminal_width = TERMINAL_WIDTH

    formatter: HelpFormatter = ctx.make_formatter()
    format_help(cmd, ctx, formatter)
    return formatter.getvalue().rstrip("\n")


def get_full_help(cmd: Command, ctx: Context) -> str:
    ctx.max_content_width = MAX_CONTENT_WIDTH
    ctx.terminal_width = TERMINAL_WIDTH

    formatter: HelpFormatter = ctx.make_formatter()
    format_full_help(cmd, ctx, formatter)
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
        max_content_width=MAX_CONTENT_WIDTH,
    )

    lines.append(f"{get_help(cmd, ctx)}\n{SEPARATOR}")
    commands: dict[str, Command] = getattr(cmd, "commands", dict())

    for sub in commands.values():
        if not sub.hidden:
            recursive_help(sub, ctx, lines)

    return f"{pretty_print(lines)}\n\n"


# noinspection PyUnusedLocal
def print_version(ctx: Context, param: Parameter, value: Any):
    if not value or ctx.resilient_parsing:
        return

    echo(f"Версия {__version__}")
    pause(PRESS_ENTER_KEY)
    ctx.exit(0)


class APIGroup(Group):
    def __init__(self, **attrs: Any):
        kwargs: dict[str, bool] = {"invoke_without_command": True, "chain": False}
        attrs.update(kwargs)
        super().__init__(**attrs)

    def format_help(self, ctx: Context, formatter: HelpFormatter) -> None:
        format_help(self, ctx, formatter)

    def format_usage(self, ctx: Context, formatter: HelpFormatter) -> None:
        format_usage(self, ctx, formatter)

    def get_usage(self, ctx: Context) -> str:
        formatter: HelpFormatter = ctx.make_formatter()
        self.format_usage(ctx, formatter)

        return formatter.getvalue().rstrip("\n")

    def format_options(self, ctx: Context, formatter: HelpFormatter) -> None:
        format_options(self, ctx, formatter)

    def format_epilog(self, ctx: Context, formatter: HelpFormatter) -> None:
        format_epilog(self, ctx, formatter)

    # noinspection PyTypeChecker
    def format_args(self, ctx: Context, formatter: HelpFormatter):
        format_args(self, ctx, formatter)

    def parse_args(self, ctx: Context, args: list[str]) -> list[str]:
        if args is None or not args:
            logger.error(
                f"Для команды {ctx.command_path} не задано ни одного аргумента или опции"
            )
            logger.error(f"Для вызова справки используется\n{ctx.command_path} --help")
            raise NoArgumentsOptionsError

        else:
            return super().parse_args(ctx, args)

    def invoke(self, ctx: Context) -> Any:
        try:
            super().invoke(ctx)

        except BaseError as e:
            logger.error(f"Ошибка {e.__class__.__name__}")
            pause(PRESS_ENTER_KEY)
            ctx.exit(1)


class SwitchArgsAPIGroup(APIGroup):
    def parse_args(self, ctx: Context, args: list[str]) -> list[str]:
        if args and not args[0].startswith("-"):
            root: str = args.pop(0)
            args.append(root)

        return super().parse_args(ctx, args)


class TermsAPIGroup(APIGroup):
    def parse_args(self, ctx: Context, args: list[str]) -> list[str]:
        if args is None:
            args: list[str] = []

        else:
            args: list[str] = list(map(up, args))

            if all(not x.startswith("-") for x in args):
                args.insert(0, "--common")

        return super().parse_args(ctx, args)


class HelpAPIGroup(APIGroup):
    def parse_args(self, ctx: Context, args: list[str]) -> list[str]:
        if args is None:
            args: list[str] = []

        return super().parse_args(ctx, args)


class MutuallyExclusiveOption(Option):
    def __init__(self, *args, **kwargs):
        self.mutually_exclusive: tuple[str, ...] = tuple(
            kwargs.pop("mutually_exclusive", tuple())
        )

        _help: str = kwargs.get("help", "")

        if self.mutually_exclusive:
            exclusive_options: str = ", ".join(
                map(prepare_option, self.mutually_exclusive)
            )

            _: dict[str, str] = {
                "help": (
                    f"{_help}.\n"
                    f"Примечание. Не может использоваться одновременно с \n"
                    f"{exclusive_options}"
                )
            }
            kwargs.update(_)

        super().__init__(*args, **kwargs)

    def handle_parse_result(
        self, ctx: Context, opts: Mapping[str, Any], args: Iterable[str]
    ) -> tuple[Any, list[str]]:
        if set(self.mutually_exclusive).intersection(opts) and self.name in opts:
            exclusive_options: str = ", ".join(
                map(prepare_option, self.mutually_exclusive)
            )

            raise UsageError(
                f"Ошибка в задании команды: `{self.name}` не может использоваться одновременно с "
                f"`{exclusive_options}`."
            )

        else:
            args: list[str] = [*args]
            ctx.terminal_width = TERMINAL_WIDTH
            ctx.max_content_width = MAX_CONTENT_WIDTH

            return super().handle_parse_result(ctx, opts, args)


@group(cls=APIGroup, help="Набор скриптов для технических писателей")
@option(
    "--version",
    is_flag=True,
    expose_value=False,
    is_eager=True,
    help="Вывести версию скрипта на экран и завершить работу",
    callback=print_version,
)
@option(
    "--debug",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг активации режима отладки." "\nПо умолчанию: False, режим отключен",
    show_default=True,
    required=False,
    default=False,
    hidden=True,
)
@help_option("-h", "--help", help=HELP, is_eager=True)
def cli(debug: bool = False):
    ctx: Context = get_current_context()

    try:
        ctx.ensure_object(dict)
        ctx.obj = dict()
        ctx.obj["debug"] = debug

        custom_logging("cli", is_debug=debug)

        result_file: bool = False

        if ctx.invoked_subcommand is None:
            echo(
                "Не указана ни одна из доступных команд. Для вызова справки используется опция -h / --help"
            )
            pause(PRESS_ENTER_KEY)
            ctx.exit(0)

        elif ctx.invoked_subcommand == "help":
            ctx.obj["full_help"] = True
            text: str = ctx.invoke(get_full_help, cmd=ctx.command, ctx=ctx)
            echo(text)
            ctx.exit(0)

        elif ctx.invoked_subcommand == "link-repair":
            result_file: bool = True

        custom_logging("cli", is_debug=debug, result_file=result_file)

    except BaseError as e:
        logger.error(f"Ошибка {e.__class__.__name__}")
        pause(PRESS_ENTER_KEY)
        ctx.exit(1)


@pass_context
def clear_logs(ctx: Context):
    keep_logs: bool = ctx.obj.get("keep_logs", False)
    debug: bool = ctx.obj.get("debug", False)
    no_result: bool = ctx.obj.get("no_result", False)
    result_file: Path = ctx.obj.get("result_file", None)

    logger.debug(
        f"Версия: {__version__}\n"
        f"Команда: {ctx.command_path}\n"
        f"Параметры: {ctx.params}"
    )

    logger.remove()

    if no_result and result_file is not None:
        result_file.unlink(missing_ok=True)

    if not keep_logs:
        rmtree(NORMAL.parent, ignore_errors=True)

    elif not debug:
        echo(f"Папка с логами: {NORMAL.parent}")

    else:
        echo(f"Папка с логами: {DEBUG.parent}")

    pause(PRESS_ENTER_KEY)
    collect()
    ctx.exit(0)
