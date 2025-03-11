# -*- coding: utf-8 -*-
from typer import Typer

from .check_russian import check_russian
from .repair_svg import repair_svg
from .table_cols import table_cols
from .version import version


def main():
    app: Typer = Typer()
    app.add_typer(check_russian, name="check-russian")
    app.add_typer(repair_svg, name="repair-svg")
    # app.add_typer(table_cols, name="table-cols")
    app.add_typer(version)
    return app
