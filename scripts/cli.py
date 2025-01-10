# -*- coding: utf-8 -*-
from operator import attrgetter
from typing import Any, Iterable, Mapping

# noinspection PyProtectedMember
from click.core import Argument, Command, Context, Group, Option, Parameter
from click.decorators import group, help_option, option
from click.exceptions import UsageError
from click.formatting import HelpFormatter
from click.globals import get_current_context
from click.termui import pause
from click.utils import echo
from loguru import logger

from __version__ import __version__
from common.constants import args_help_dict, HELP, PRESS_ENTER_KEY
from common.custom_logger import custom_logging

COL_SPACING: int = 3
COL_MAX: int = 38
MAX_CONTENT_WIDTH: int = 100
TERMINAL_WIDTH: int = 100

SEPARATOR: str = "-" * MAX_CONTENT_WIDTH


def up(value: str):
    return value.upper() if not value.startswith("--") else value


def underscore_to_dash(value: str, *, prefix: bool = True):
    return f'{int(prefix) * "--"}{value.replace("_", "-")}'


def format_usage(cmd: Command, ctx: Context, formatter: HelpFormatter) -> None:
    args: list[str] = []
    opts: list[str] = []

    for param in cmd.params:
        if param.name == "help":
            continue

        elif param.param_type_name == "option":
            _opts: str = "/".join(param.opts)

            if param.type.name != "boolean":
                _metavar: str = f" {param.make_metavar()}"

            elif param.name not in ("version", "help"):
                _metavar: str = f"/--no-{underscore_to_dash(param.name, prefix=False)}"

            else:
                _metavar: str = ""

            _param: str = f"{_opts}{_metavar}"
            opts.append(_param)

        else:
            _param: str = f"<{param.make_metavar()}>"
            args.append(_param)

    args_str: str = " ".join(args) if args else ""
    opts_str: str = "\n".join(opts) if opts else ""

    formatter.write(f"Использование:\n{ctx.command_path} {args_str}\n{opts_str}\n")


def format_options(cmd: Command, ctx: Context, formatter: HelpFormatter) -> None:
    def modify_help_record(parameter: Parameter):
        if isinstance(parameter, Argument):
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
        with formatter.section("Опции"):
            col_spacing: int = COL_SPACING
            col_max: int = COL_MAX
            formatter.write_dl(rows, col_max, col_spacing)


def format_epilog(cmd: Command, parent: Context = None, formatter: HelpFormatter = None) -> None:
    if parent is None:
        parent: Context = get_current_context()

    if formatter is None:
        formatter: HelpFormatter = parent.make_formatter()

    commands: dict[str, Command] = getattr(cmd, "commands", dict())

    if commands != dict():
        with formatter.section("Подкоманды"):
            rows: list[tuple[str, str]] = [
                (sub.name, sub.help)
                for sub in sorted(commands.values(), key=attrgetter("name"))
                if not sub.hidden]
            col_spacing: int = COL_SPACING
            col_max: int = COL_MAX

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
        if param.param_type_name == "argument"]

    if args:
        keys: list[str] = [item.removesuffix(".exe") for item in ctx.command_path.split(" ")]
        rows: list[tuple[str, str]] = [
            (arg.name, args_help_dict.get_multiple_keys(keys=keys).get(arg.name))
            for arg in args]

        col_spacing: int = COL_MAX - max(map(len, map(attrgetter("name"), args)))
        echo(f"{col_spacing=}")
        col_max: int = COL_MAX

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
        self.format_usage(ctx, formatter)
        self.format_help_text(ctx, formatter)
        self.format_args(ctx, formatter)
        self.format_options(ctx, formatter)
        self.format_epilog(ctx, formatter)

        if hasattr(self, "commands"):
            formatter.write(f"{SEPARATOR}\n\n")

            for command_name in sorted(self.commands):
                command: Command = self.commands.get(command_name)

                if not command.hidden:
                    formatter.write(recursive_help(command, ctx))

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

    def parse_args(self, ctx, args):
        if self.__class__.__name__ == "APIGroup" and args is not None and args[0] in self.commands:
            if len(args) == 1 or args[-1] not in self.commands:
                # args.append('')
                pass

        super().parse_args(ctx, args)


class TermsAPIGroup(APIGroup):
    def parse_args(self, ctx, args):
        args: list[str] = list(map(up, args))

        if args is not None and all(not x.startswith("--") for x in args):
            args.insert(0, '--common')

        echo(f"{args=}")
        super().parse_args(ctx, args)


class MutuallyExclusiveOption(Option):
    def __init__(self, *args, **kwargs):
        self.mutually_exclusive: set[str] = set(kwargs.pop("mutually_exclusive", []))

        _help: str = kwargs.get("help", "")

        if self.mutually_exclusive:
            exclusive_options: str = ", ".join(map(underscore_to_dash, self.mutually_exclusive))

            _: dict[str, str] = {
                "help": f"{_help}\nПримечание. Аргумент не может использоваться одновременно с {exclusive_options}"}
            kwargs.update(_)

        super().__init__(*args, **kwargs)

    def handle_parse_result(
            self,
            ctx: Context,
            opts: Mapping[str, Any],
            args: Iterable[str]) -> tuple[Any, list[str]]:
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            exclusive_options: str = ", ".join(map(underscore_to_dash, self.mutually_exclusive))

            raise UsageError(
                f"Ошибка в задании команды: `{self.name}` не может использоваться одновременно с "
                f"`{exclusive_options}`."
            )

        else:
            args: list[str] = [*args]
            return super().handle_parse_result(ctx, opts, args)


@group(
    cls=APIGroup,
    help="""Набор скриптов для технических писателей""")
@option(
    "-v", "--version",
    is_flag=True,
    expose_value=False,
    is_eager=True,
    help="""Вывести версию скрипта на экран и завершить работу""",
    callback=print_version)
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
@logger.catch
@custom_logging("cli", is_debug=True)
def command_line_interface(**kwargs):
    ctx: Context = get_current_context()
    ctx.ensure_object(dict)
    ctx.obj = dict(**kwargs)

    echo(f"{ctx.command_path=}")
    echo(f"{ctx.invoked_subcommand=}")

    if ctx.invoked_subcommand is None:
        echo("Не указана ни одна из доступных команд. Для вызова справки используется опция -h / --help")
        pause(PRESS_ENTER_KEY)
        ctx.exit(0)

    else:
        logger.debug(f"Команда: {ctx.command_path}")
