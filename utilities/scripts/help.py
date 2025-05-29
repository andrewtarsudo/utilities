# -*- coding: utf-8 -*-
from click.core import Context
from click.decorators import pass_context

from utilities import echo
from utilities.scripts.api_group import format_full_help, NoArgsAPIGroup
from utilities.scripts.cli import cli


@cli.command(
    "help",
    cls=NoArgsAPIGroup,
    help="Команда для вызова полной справки",
    add_help_option=False)
@pass_context
def help_command(ctx: Context):
    ctx.obj["full_help"] = True
    echo(ctx.obj)
    ctx.invoke(format_full_help)
