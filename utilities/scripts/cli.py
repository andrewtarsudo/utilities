# -*- coding: utf-8 -*-

from click.core import Context
from click.decorators import group, help_option, option
from click.globals import get_current_context
from click.termui import pause
from click.types import BOOL
from click.utils import echo
from loguru import logger

from utilities.common.auto_update import check_updates
from utilities.common.custom_logger import custom_logging
from utilities.common.errors import BaseError
from utilities.common.shared import HELP, PRESS_ENTER_KEY
from utilities.scripts.api_group import APIGroup, get_full_help, print_version


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
        ctx.obj = {"debug": debug, "temp_dir": "_temp/"}

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

        elif ctx.invoked_subcommand == "link-repair":
            result_file: bool = True

        custom_logging("cli", is_debug=debug, result_file=result_file)
        updated: bool = check_updates(ctx)

        if updated:
            pause("Введите повторно свою команду")
            ctx.exit(0)

    except BaseError as e:
        logger.error(f"Ошибка {e.__class__.__name__}")
        pause(PRESS_ENTER_KEY)
        ctx.exit(1)
