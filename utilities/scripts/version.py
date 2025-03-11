# -*- coding: utf-8 -*-
from rich.prompt import Prompt
from rich import print
from typer.main import Typer
from click.exceptions import Exit
from utilities.common.constants import __version__, PRESS_ENTER_KEY

version: Typer = Typer()


@version.command(
    name="version",
    help="Вывести версию скрипта на экран и завершить работу")
def version_command():
    print(f"Версия {__version__}")
    Prompt.ask(PRESS_ENTER_KEY)
    raise Exit(0)
