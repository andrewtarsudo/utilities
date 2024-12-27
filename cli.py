from operator import attrgetter
from typing import Any, Iterable

from click.core import Argument, Command, Context, Group, Parameter
from click.decorators import group, help_option, option
from click.formatting import HelpFormatter
from click.globals import get_current_context
from click.termui import pause, style
from click.utils import echo
from loguru import logger

from __version__ import __version__
from constants import PRESS_ENTER_KEY, args_help_dict


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
                _metavar: str = f"/--no-{param.name}"
            else:
                _metavar: str = ""

            _param: str = f"{_opts}{_metavar}"
            opts.append(_param)

        else:
            _param: str = f"<{param.make_metavar()}>"
            args.append(_param)

    args_str: str = " ".join(args) if args else ""

    if cmd.name == "translate":
        opts_str: str = "\n".join(opts) if opts else ""
        formatter.write(f"Использование:\n{ctx.command_path}{args_str}\n{opts_str}\n")

    else:
        opts_str: str = " ".join(opts) if opts else ""
        formatter.write(f"Использование:\n{ctx.command_path} {args_str}{opts_str}\n")


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
            rows.append(("-h, --help", "Вывести справочную информацию на экран и завершить работу"))

    if rows:
        with formatter.section("Опции"):
            opt_names: list[str] = [item[0] for item in rows]
            col_spacing: int = 30 - max(map(len, opt_names))
            col_max: int = 80
            formatter.write_dl(rows, col_max, col_spacing)


def format_epilog(cmd: Command, parent: Context = None, formatter: HelpFormatter = None) -> None:
    if parent is None:
        parent: Context = get_current_context()

    if formatter is None:
        formatter: HelpFormatter = parent.make_formatter()

    commands: dict[str, Command] = getattr(cmd, "commands", dict())

    if commands != dict():
        with formatter.section("Подкоманды"):
            sub_names: list[str] = [sub.name for sub in commands.values() if not sub.hidden]

            rows: list[tuple[str, str]] = [
                (sub.name, sub.help) for sub in sorted(commands.values(), key=attrgetter("name")) if not sub.hidden]
            col_spacing: int = 30 - max(map(len, sub_names))
            col_max: int = 80

            formatter.write_dl(rows, col_max, col_spacing)


# noinspection PyTypeChecker
def format_args(cmd: Command, ctx: Context, formatter: HelpFormatter):
    args: list[Argument] = [param for param in cmd.get_params(ctx) if param.param_type_name == "argument"]

    if args:
        args_names: list[str] = [arg.name for arg in args]
        keys: list[str] = [item.removesuffix(".exe") for item in ctx.command_path.split(" ")]

        rows: list[tuple[str, str]] = [
            (arg.name, args_help_dict.get_multiple_keys(keys=keys).get(arg.name)) for arg in args]
        col_spacing: int = 30 - max(map(len, args_names))
        col_max: int = 80

        with formatter.section("Аргументы"):
            formatter.write_dl(rows, col_max, col_spacing)
    return


def format_help(cmd: Command, ctx: Context, formatter: HelpFormatter) -> None:
    format_usage(cmd, ctx, formatter)
    cmd.format_help_text(ctx, formatter)
    format_args(cmd, ctx, formatter)
    format_options(cmd, ctx, formatter)
    format_epilog(cmd, ctx, formatter)


def get_help(cmd: Command, ctx: Context) -> str:
    formatter = ctx.make_formatter()
    format_help(cmd, ctx, formatter)
    return formatter.getvalue().rstrip("\n")


def recursive_help(cmd: Command, parent: Context = None, lines: Iterable[str] = None):
    if lines is None:
        lines: list[str] = []

    else:
        lines: list[str] = [*lines]

    ctx: Context = Context(cmd, info_name=cmd.name, parent=parent, color=True)

    if cmd.name == "translate":
        lines.append(style(get_help(cmd, ctx), fg="green", bold=True))

    else:
        lines.append(get_help(cmd, ctx))

    lines.append("-" * 80)
    lines.append("\n")
    commands: dict[str, Command] = getattr(cmd, "commands", dict())

    for sub in commands.values():
        if not sub.hidden:
            recursive_help(sub, ctx, lines)

    return "\n".join(lines)


def print_version(ctx: Context, param: Parameter, value: Any):
    if not value or ctx.resilient_parsing:
        return

    echo(f"Версия {__version__}")
    pause(PRESS_ENTER_KEY)
    ctx.exit(0)


class APIGroup(Group):
    def format_help(self, ctx: Context, formatter: HelpFormatter) -> None:
        self.format_usage(ctx, formatter)
        self.format_help_text(ctx, formatter)
        self.format_args(ctx, formatter)
        self.format_options(ctx, formatter)
        self.format_epilog(ctx, formatter)

        if hasattr(self, "commands"):
            lines: tuple[str, ...] = ("-" * 80, "\n")
            formatter.write("\n".join(lines))

            del lines

            command_names: list[str] = [*self.commands.keys()]

            if "translate" in command_names:
                command_names.sort()
                index: int = command_names.index("translate")
                translate: str = command_names.pop(index)
                command_names.insert(0, translate)

            for command_name in command_names:
                command: Command = self.commands.get(command_name)

                if not command.hidden:
                    formatter.write(recursive_help(command, ctx))

            del command_names

    def format_usage(self, ctx: Context, formatter: HelpFormatter) -> None:
        format_usage(self, ctx, formatter)

    def get_usage(self, ctx: Context) -> str:
        formatter = ctx.make_formatter()
        format_usage(self, ctx, formatter)
        return formatter.getvalue().rstrip("\n")

    def format_options(self, ctx: Context, formatter: HelpFormatter) -> None:
        format_options(self, ctx, formatter)

    def format_epilog(self, ctx: Context, formatter: HelpFormatter) -> None:
        format_epilog(self, ctx, formatter)

    # noinspection PyTypeChecker
    def format_args(self, ctx: Context, formatter: HelpFormatter):
        format_args(self, ctx, formatter)


@group(
    cls=APIGroup,
    help="""Скрипт для работы с Yandex Translate API""",
    invoke_without_command=True)
@option(
    "-v", "--version",
    is_flag=True,
    expose_value=False,
    is_eager=True,
    help="""Вывести версию скрипта на экран и завершить работу""",
    callback=print_version)
@help_option(
    "-h", "--help",
    help="Вывести справочную информацию на экран и завершить работу",
    is_eager=True)
def command_line_interface(**kwargs):
    ctx: Context = get_current_context()
    ctx.ensure_object(dict)
    ctx.obj = dict(**kwargs)

    if ctx.invoked_subcommand is None:
        echo("Не указана ни одна из доступных команд. Для вызова справки используйте опцию -h или --help")
        pause(PRESS_ENTER_KEY)
        ctx.exit(0)

    else:
        logger.debug(f"Команда: {ctx.command_path}")
