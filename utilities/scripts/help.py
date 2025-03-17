# -*- coding: utf-8 -*-
from click.core import Context
from click.decorators import pass_context
from click.termui import echo

from utilities.scripts.cli import cli, format_full_help, HelpAPIGroup


@cli.command(
    "help",
    cls=HelpAPIGroup,
    help="Команда для вызова полной справки",
    add_help_option=False)
@pass_context
def help_command(ctx: Context):
    ctx.obj["full_help"] = True
    echo(ctx.obj)
    ctx.invoke(format_full_help)
