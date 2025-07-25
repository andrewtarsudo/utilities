# -*- coding: utf-8 -*-
from functools import partial
from pathlib import Path
from shutil import rmtree
from typing import Any, Iterable, Mapping

from click.core import Argument, Command, Context, echo, Group, Option, Parameter
from click.decorators import pass_context
from click.exceptions import UsageError
from click.formatting import HelpFormatter
from click.globals import get_current_context
from click.shell_completion import CompletionItem
from click.termui import pause, style
from loguru import logger
from more_itertools import flatten

from utilities.common.config_file import config_file, ConfigFile
from utilities.common.errors import BaseError, CommandNotFoundError, ConditionalOptionError, \
    MutuallyExclusiveOptionError, NoArgumentsOptionsError
from utilities.common.functions import get_version, is_windows, pretty_print
from utilities.common.shared import HELP, MyYAML, PRESS_ENTER_KEY
from utilities.scripts.args_help_dict import args_help_dict

COL_MAX: int = config_file.get_general("col_max")
MAX_CONTENT_WIDTH: int = config_file.get_general("max_content_width")
TERMINAL_WIDTH: int = config_file.get_general("terminal_width")

SEPARATOR: str = "-" * MAX_CONTENT_WIDTH


def prepare_option(value: str, *, prefix: bool = True, remove_suffix: str | None = "-flag"):
    value: str = value.replace("_", "-")

    if remove_suffix is not None:
        value: str = value.removesuffix(remove_suffix)

    return style(f'{int(prefix) * "--"}{value}', fg="magenta", bold=True)


def wrap_line(line: str):
    if len(line) >= MAX_CONTENT_WIDTH:
        pipe_indexes: list[int] = [index for index, char in enumerate(line) if char == "|"]
        index: int = max(filter(lambda x: x <= MAX_CONTENT_WIDTH, pipe_indexes))
        line: str = f"{line[:index + 1]}\n{wrap_line(line[index + 2:])}"

    return line


# noinspection PyUnusedLocal
@pass_context
def clear_logs(ctx):
    keep_logs: bool = ctx.obj.get("keep_logs", False)
    debug: bool = ctx.obj.get("debug", False)
    no_result: bool = ctx.obj.get("no_result", False)
    result_file: Path | None = ctx.obj.get("result_file", None)

    general_temp_dir: str = Path(config_file.get_general("temp_dir")).expanduser().as_posix()
    update_temp_dir: str = Path(config_file.get_update("temp_dir")).expanduser().as_posix()
    rmtree(general_temp_dir, ignore_errors=True)
    rmtree(update_temp_dir, ignore_errors=True)

    log_path: Path = Path(config_file.get_general("log_path")).parent
    debug_log_folder: Path = Path(config_file.get_general("debug_log_folder")).parent

    logger.remove()

    if no_result and result_file is not None:
        result_file.unlink(missing_ok=True)

    if not keep_logs:
        rmtree(log_path, ignore_errors=True)

    elif not debug:
        echo(f"\nПапка с логами: {log_path}\n")

    else:
        echo(f"\nПапка с логами: {debug_log_folder}\n")

    rmtree(config_file.get_general("temp_dir"), ignore_errors=True)
    # input(PRESS_ENTER_KEY)


def format_usage(
        cmd: Command,
        ctx: Context,
        formatter: HelpFormatter) -> None:
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
    suffix: str = ".exe" * int(is_windows())
    name: str = ctx.command_path.replace("__main__.py", f"tw_utilities{suffix}")

    if commands is not None and commands:
        commands_str: str = wrap_line(" | ".join(f"<{command}>" for command in sorted(commands)))
        formatter.write(
            f"{style('Использование', fg='bright_cyan', bold=True)}:"
            f"\n{name} {wrap_line(opts_str)}"
            f"\n{commands_str}\n")

    elif cmd.name != "help":
        formatter.write(
            f"{style('Использование', fg='bright_cyan', bold=True)}:"
            f"\n{name} {args_str}"
            f"\n{wrap_line(opts_str)}\n")

    else:
        formatter.write(
            f"{style('Использование', fg='bright_cyan', bold=True)}:"
            f"\n{name}\n")


def format_options(
        cmd: Command,
        ctx: Context,
        formatter: HelpFormatter) -> None:
    def modify_help_record(parameter: Parameter):
        if isinstance(parameter, Argument):
            return None

        elif isinstance(parameter, Option) and parameter.hidden:
            return None

        option_help: str
        _, option_help = parameter.get_help_record(ctx)

        try:
            _default: int = option_help.index("[default")

        except ValueError:
            pass

        else:
            option_help: str = option_help[:_default]

        try:
            _required: int = option_help.index(" [required]")

        except ValueError:
            pass

        else:
            option_help: str = option_help[:_required]
            _: str = f"{_} (*)"

        return style(_, fg="cyan", bold=True), option_help

    rows: list[tuple[str, str]] = []

    for param in cmd.get_params(ctx):
        if param.name != "help":
            rv: tuple[str, str] = modify_help_record(param)

            if rv is not None:
                rows.append(rv)
                rows.append(("", ""))

        else:
            rows.append((style("-h, --help", fg="cyan", bold=True), HELP))

    if rows:
        formatter.width = MAX_CONTENT_WIDTH

        with formatter.section(style("Опции", fg="blue", bold=True)):
            opt_names: list[str] = [item[0] for item in rows]

            col_spacing: int = COL_MAX - max(map(len, opt_names)) - 4
            col_max: int = MAX_CONTENT_WIDTH
            formatter.write_dl(rows, col_max, col_spacing)


def join_names(cmd: Command, aliases: dict[Command, set[str]]):
    names: str = " / ".join(aliases.get(cmd)) if cmd in aliases else None

    if names:
        names: str = f" / {names}"

    return f"{cmd.name}{names}"


def format_epilog(
        cmd: Command,
        parent: Context = None,
        formatter: HelpFormatter = None) -> None:
    if parent is None:
        parent: Context = get_current_context()

    if formatter is None:
        formatter: HelpFormatter = parent.make_formatter()

    formatter.width = MAX_CONTENT_WIDTH

    commands: dict[str, Command] = getattr(cmd, "commands", dict())
    aliases: dict[Command, set[str]] = getattr(cmd.__class__, "aliases", {})

    if commands:
        dict_commands: dict[Command, str] = {
            command: join_names(command, aliases)
            for command in sorted(commands.values(), key=lambda x: x.name)
            if not command.hidden}

        with formatter.section(style("Подкоманды", fg="green", bold=True)):
            rows: list[tuple[str, str]] = [
                (style(v, fg="green", bold=True),
                 style(k.help, fg="green", bold=True))
                for k, v in dict_commands.items()]

            col_spacing: int = COL_MAX - 2 * max(map(len, dict_commands.values())) + 11
            col_max: int = MAX_CONTENT_WIDTH

            formatter.write_dl(rows, col_max, col_spacing)


def format_help(
        cmd: Command,
        ctx: Context,
        formatter: HelpFormatter) -> None:
    format_usage(cmd, ctx, formatter)
    cmd.format_help_text(ctx, formatter)
    format_args(cmd, ctx, formatter)
    format_options(cmd, ctx, formatter)
    format_epilog(cmd, ctx, formatter)


def format_full_help(
        cmd: Command,
        ctx: Context,
        formatter: HelpFormatter) -> None:
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
def format_args(
        cmd: Command,
        ctx: Context,
        formatter: HelpFormatter):
    args: list[Argument] = [
        param for param in cmd.get_params(ctx)
        if isinstance(param, Argument)]

    if args:
        formatter.width = MAX_CONTENT_WIDTH
        asterisk: str = style("(*)", fg="red", bold=True)

        keys: list[str] = [item.removesuffix(".exe") for item in ctx.command_path.split(" ")]
        rows: list[tuple[str, str]] = [
            (f"{style(arg.name, fg='cyan', bold=True)} {asterisk}",
             args_help_dict.get_multiple_keys(keys=keys).get(arg.name))
            for arg in args]

        args_names: list[str] = [arg.name for arg in args]

        col_spacing: int = COL_MAX - args_help_dict.max_key - max(map(len, args_names)) - 5
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
        max_content_width=MAX_CONTENT_WIDTH)

    lines.append(f"{get_help(cmd, ctx)}\n{SEPARATOR}")
    commands: dict[str, Command] = getattr(cmd, "commands", {})

    for sub in commands.values():
        if not sub.hidden:
            recursive_help(sub, ctx, lines)

    return f"{pretty_print(lines)}\n\n"


# noinspection PyUnusedLocal
def print_version(ctx: Context, param: Parameter, value: Any):
    if not value or ctx.resilient_parsing:
        return

    echo(f"Версия {get_version()}")
    pause(PRESS_ENTER_KEY)
    ctx.exit(0)


class APIGroup(Group):
    aliases: dict[Command, set[str]] = {}

    @classmethod
    def all_alias_names(cls) -> set[str]:
        return set(flatten(cls.aliases.values()))

    @classmethod
    def from_alias(cls, cmd_name: str) -> Command | None:
        for k, v in cls.aliases.items():
            if cmd_name in v:
                return k

        else:
            return None

    def get_aliases(self, ctx: Context, cmd_name: str):
        if cmd_name in self.list_commands(ctx):
            cmd: Command = self.get_command(ctx, cmd_name)

        elif cmd_name in self.__class__.all_alias_names():
            cmd: Command = self.__class__.from_alias(cmd_name)

        else:
            raise KeyError

        aliases: set[str] | None = self.__class__.aliases.get(cmd, None)

        if aliases is None:
            return f"{cmd.name}"

        else:
            return f"{cmd.name} / {' / '.join(aliases)}"

    def __init__(self, aliases: set[str] = None, **attrs: Any):
        kwargs: dict[str, bool] = {
            "invoke_without_command": True,
            "chain": False}
        attrs.update(kwargs)

        context_settings: dict[str, str] = {
            "auto_envvar_prefix": "TW_UTILITIES"}

        super().__init__(context_settings=context_settings, **attrs)

        if aliases is None:
            aliases: set[str] = set()

        self.__class__.aliases[self] = aliases
        self.config_file: ConfigFile = config_file

    def get_command(self, ctx: Context, cmd_name: str) -> Command | None:
        if cmd_name in self.list_commands(ctx):
            return self.commands.get(cmd_name, None)

        elif cmd_name in self.__class__.all_alias_names():
            return self.__class__.from_alias(cmd_name)

        else:
            logger.error(f"Подкоманда {cmd_name} не найдена")
            raise CommandNotFoundError

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
        if self.epilog:
            super().format_epilog(ctx, formatter)

    # noinspection PyTypeChecker
    def format_args(self, ctx: Context, formatter: HelpFormatter):
        format_args(self, ctx, formatter)

    def parse_args(self, ctx: Context, args: list[str]) -> list[str]:
        if args is None or not args:
            logger.error(f"Для команды {ctx.command_path} не задано ни одного аргумента или опции")
            logger.error(f"Для вызова справки используется\n{ctx.command_path} --help")
            raise NoArgumentsOptionsError

        return super().parse_args(ctx, args)

    def invoke(self, ctx: Context) -> Any:
        for param in self.params:
            if isinstance(param, Option) and param.default:
                param.default = self.config_file.get_commands(
                    ctx.invoked_subcommand,
                    param.name)

        try:
            super().invoke(ctx)

        except BaseError as e:
            logger.error(f"Ошибка {e.__class__.__name__}")
            pause(PRESS_ENTER_KEY)
            ctx.exit(1)

        else:
            ctx.obj["success"] = True

    def shell_complete(self, ctx: Context, incomplete: str) -> list[CompletionItem]:
        commands: list[CompletionItem] = [
            CompletionItem(cmd_name)
            for cmd_name in self.list_commands(ctx)
            if cmd_name.startswith(incomplete)]

        params: list[CompletionItem] = [
            CompletionItem(param)
            for param in self.params
            if param.opts[0].startswith(incomplete) or param.opts[0].startswith(incomplete)]

        return [*commands, *params]

    def resolve_command(
            self,
            ctx: Context,
            args: list[str]) -> tuple[str | None, Command | None, list[str]]:
        try:
            return super().resolve_command(ctx, args)

        except UsageError as e:

            yaml: MyYAML = MyYAML(typ="safe")
            ctx_info: str = yaml.dump(
                e.ctx.to_info_dict(),
                indent=2,
                width=120)

            logger.error("Ошибка обработки команды")
            logger.debug(
                f"Параметры команд:"
                f"\n{ctx_info}")
            raise CommandNotFoundError


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
            options: list[str] = []
            non_options: list[str] = []

            for arg in args:
                if not arg.startswith("-"):
                    non_options.append(arg.upper())

                else:
                    options.append(arg)

            if not options:
                options.append("--common")

            args: list[str] = [*options, *non_options]

        return super().parse_args(ctx, args)


class NoArgsAPIGroup(APIGroup):
    def parse_args(self, ctx: Context, args: list[str]) -> list[str]:
        return super().parse_args(ctx, [])


class MutuallyExclusiveOption(Option):
    def __init__(self, *args, **kwargs):
        self.mutually_exclusive: tuple[str, ...] = tuple(kwargs.pop("mutually_exclusive", tuple()))

        _help: str = kwargs.get("help", "")

        if self.mutually_exclusive:
            exclusive_options: str = ", ".join(map(prepare_option, self.mutually_exclusive))

            _: dict[str, str] = {
                "help": (
                    f"{_help}."
                    f"\nПримечание. Не может использоваться одновременно с "
                    f"\n{exclusive_options}")}
            kwargs.update(_)

        super().__init__(*args, **kwargs)

    def handle_parse_result(
            self,
            ctx: Context,
            opts: Mapping[str, Any],
            args: Iterable[str]) -> tuple[Any, list[str]]:
        if set(self.mutually_exclusive).intersection(opts) and self.name in opts:
            exclusive_options: str = ", ".join(map(prepare_option, self.mutually_exclusive))

            logger.error(
                f"Ошибка в задании команды: `{self.name}` не может использоваться одновременно с "
                f"`{exclusive_options}`.")
            raise MutuallyExclusiveOptionError

        else:
            args: list[str] = [*args]
            ctx.terminal_width = TERMINAL_WIDTH
            ctx.max_content_width = MAX_CONTENT_WIDTH

            return super().handle_parse_result(ctx, opts, args)


class ConditionalOption(Option):
    def __init__(self, *args, **kwargs):
        self.conditional: tuple[str, ...] = tuple(kwargs.pop("conditional", ()))

        _help: str = kwargs.get("help", "")

        if self.conditional:
            prepare: partial = partial(prepare_option, prefix=False)

            exclusive_options: str = ", ".join(map(prepare, self.conditional))

            _: dict[str, str] = {
                "help": (
                    f"{_help}."
                    f"\nПримечание. Этот параметр или хотя бы один из"
                    f"\n{exclusive_options} должен быть задан")}
            kwargs.update(_)

        super().__init__(*args, **kwargs)

    def handle_parse_result(
            self,
            ctx: Context,
            opts: Mapping[str, Any],
            args: Iterable[str]) -> tuple[Any, list[str]]:
        if set(self.conditional).intersection(opts):
            args: list[str] = [*args]
            ctx.terminal_width = TERMINAL_WIDTH
            ctx.max_content_width = MAX_CONTENT_WIDTH

            return super().handle_parse_result(ctx, opts, args)

        else:
            prepare: partial = partial(prepare_option, prefix=False)
            conditional_options: str = ", ".join(map(prepare, self.conditional))

            logger.error(
                f"Ошибка в задании команды: `{self.name}` или хотя бы один из "
                f"`{conditional_options}` должен быть задан.")
            raise ConditionalOptionError
