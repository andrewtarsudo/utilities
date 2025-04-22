# -*- coding: utf-8 -*-

from click.exceptions import Exit
from click.globals import get_current_context
from loguru import logger
from rich import print
from rich.prompt import Prompt
from typer.main import Typer
from typer.models import Context

from utilities.common.errors import BaseError
from utilities.common.custom_logger import custom_logging
from utilities.common.constants import PRESS_ENTER_KEY
from utilities.scripts.check_russian import check_russian
from utilities.scripts.convert_tables import convert_tables
from utilities.scripts.filter_images import filter_images
from utilities.scripts.format_code import format_code
from utilities.scripts.link_repair import link_repair
from utilities.scripts.list_files import list_files
from utilities.scripts.main_group import MainGroup
from utilities.scripts.reduce_image import reduce_image
from utilities.scripts.repair_svg import repair_svg
from utilities.scripts.table_cols import table_cols
from utilities.scripts.terms import terms
from utilities.scripts.validate_yaml_file import validate_yaml
from utilities.scripts.version import version

app: Typer = Typer(cls=MainGroup, add_help_option=True)


def main():
    app.add_typer(check_russian, cls=MainGroup, add_help_option=True)
    app.add_typer(convert_tables, cls=MainGroup, add_help_option=True)
    app.add_typer(filter_images, cls=MainGroup, add_help_option=True)
    app.add_typer(format_code, cls=MainGroup, add_help_option=True)
    app.add_typer(link_repair, cls=MainGroup, add_help_option=True)
    app.add_typer(list_files, cls=MainGroup, add_help_option=True)
    app.add_typer(reduce_image, cls=MainGroup, add_help_option=True)
    app.add_typer(repair_svg, cls=MainGroup, add_help_option=True)
    app.add_typer(table_cols, cls=MainGroup, add_help_option=True)
    app.add_typer(terms, cls=MainGroup, add_help_option=True)
    app.add_typer(validate_yaml, cls=MainGroup, add_help_option=True)
    app.add_typer(version)
    return app()


@app.callback()
def set_ctx_logging(debug: bool = False):
    try:
        ctx: Context = get_current_context(silent=True)
        ctx.ensure_object(dict)
        ctx.obj = dict()
        ctx.obj["debug"] = debug

        custom_logging("cli", is_debug=debug)

        result_file: bool = False

        if ctx.invoked_subcommand is None:
            print("Не указана ни одна из доступных команд. Для вызова справки используется опция -h / --help")
            Prompt.ask(PRESS_ENTER_KEY)
            raise Exit(0)

        if ctx.invoked_subcommand == "link-repair":
            result_file: bool = True

        custom_logging("cli", is_debug=debug, result_file=result_file)

    except BaseError as e:
        logger.error(f"Ошибка {e.__class__.__name__}, {str(e)}")
        Prompt.ask(PRESS_ENTER_KEY)
        raise Exit(1)
