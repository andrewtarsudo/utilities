# -*- coding: utf-8 -*-
from pathlib import Path
from shutil import rmtree

from click.core import Context
from click.decorators import group, help_option, option, pass_context
from click.globals import get_current_context
from click.shell_completion import add_completion_class
from click.termui import pause
from click.types import BOOL
from click.utils import echo
from loguru import logger

from utilities.common.custom_logger import custom_logging
from utilities.common.errors import BaseError
from utilities.common.functions import get_version
from utilities.common.shared import DEBUG, HELP, NORMAL, PRESS_ENTER_KEY
from utilities.scripts.completion import PowershellComplete
from utilities.scripts.api_group import APIGroup, get_full_help, install_completion, NoArgsAPIGroup, print_version


@group(
    cls=APIGroup,
    help="Набор скриптов для технических писателей")
@option(
    "--version",
    is_flag=True,
    expose_value=False,
    is_eager=True,
    help="Вывести версию скрипта на экран и завершить работу",
    callback=print_version)
@option(
    "--debug",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг активации режима отладки."
         "\nПо умолчанию: False, режим отключен",
    show_default=True,
    required=False,
    default=False,
    hidden=True)
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
def cli(debug: bool = False):
    ctx: Context = get_current_context()

    try:
        ctx.ensure_object(dict)
        ctx.obj = {"debug": debug}

        result_file: bool = False

        if ctx.invoked_subcommand is None:
            echo("Не указана ни одна из доступных команд. Для вызова справки используется опция -h / --help")
            pause(PRESS_ENTER_KEY)
            ctx.exit(0)

        elif ctx.invoked_subcommand == "help":
            ctx.obj["full_help"] = True
            text: str = ctx.invoke(get_full_help, cmd=ctx.command, ctx=ctx)
            echo(text)
            ctx.exit(0)

        elif ctx.invoked_subcommand == "install":
            ctx.invoke(install_command)
            echo("install")
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
        f"Версия: {get_version()}\n"
        f"Команда: {ctx.command_path}\n"
        f"Параметры: {ctx.params}")

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
    ctx.exit(0)


# noinspection PyUnusedLocal
@cli.command(
    "install",
    cls=NoArgsAPIGroup,
    help="Команда для вызова полной справки",
    add_help_option=False)
@pass_context
def install_command(ctx: Context):
    add_completion_class(PowershellComplete)
    ctx.obj["full_help"] = True
    ctx.invoke(install_completion, ctx=ctx)
