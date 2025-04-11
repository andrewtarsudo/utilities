# -*- coding: utf-8 -*-
from click.core import Context
from click.decorators import pass_context

from utilities.scripts.cli import cli, completion_powershell, NoArgsAPIGroup


@cli.command(
    "install-completion",
    cls=NoArgsAPIGroup,
    help="Команда для добавления автодополнения",
    add_help_option=False)
@pass_context
def install_completion_command(ctx: Context):
    ctx.invoke(completion_powershell)
