# -*- coding: utf-8 -*-
from typer.main import Typer

from .convert_tables import convert_tables
from .check_russian import check_russian
from .filter_images import filter_images
from .format_code import format_code
from .link_repair import link_repair
from .list_files import list_files
from .reduce_image import reduce_image
from .repair_svg import repair_svg
from .table_cols import table_cols
from .terms import terms
from .validate_yaml_file import validate_yaml
from .version import version


def main():
    app: Typer = Typer()
    app.add_typer(check_russian, name="check-russian")
    app.add_typer(convert_tables, name="convert-tables")
    app.add_typer(filter_images, name="filter-images")
    app.add_typer(format_code, name="format-code")
    app.add_typer(link_repair, name="link-repair")
    app.add_typer(list_files, name="list-files")
    app.add_typer(reduce_image, name="reduce-image")
    app.add_typer(repair_svg, name="repair-svg")
    app.add_typer(table_cols, name="table-cols")
    app.add_typer(terms, name="terms")
    app.add_typer(validate_yaml, name="validate-yaml")
    app.add_typer(version)
    return app
