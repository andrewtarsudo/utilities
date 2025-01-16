# -*- coding: utf-8 -*-
from pathlib import Path
from re import DOTALL, MULTILINE, sub
from typing import Iterable

from click import echo, option
from click.core import Context
from click.decorators import help_option, pass_context
from click.termui import pause
from click.types import BOOL, Path as ClickPath
from loguru import logger

from utilities.common.constants import HELP, PRESS_ENTER_KEY, StrPath
from utilities.common.functions import get_files
from utilities.scripts.cli import APIGroup, clear_logs, command_line_interface


@command_line_interface.command(
    "repair-svg",
    cls=APIGroup,
    help="Команда для исправления файлов SVG",
    invoke_without_command=True)
@option(
    "-f", "--file", "files",
    type=ClickPath(
        exists=True,
        file_okay=True,
        readable=True,
        resolve_path=True,
        allow_dash=False,
        dir_okay=False),
    help="\b\nФайл для обработки. Может использоваться несколько раз",
    multiple=True,
    required=False,
    metavar="<FILE> ... <FILE>",
    default=None)
@option(
    "-d", "--dir", "directory",
    type=ClickPath(
        exists=True,
        file_okay=False,
        resolve_path=True,
        allow_dash=False,
        dir_okay=True),
    help="Директория для обработки",
    multiple=False,
    required=False,
    metavar="<DIR>",
    default=None)
@option(
    "--recursive/--no-recursive",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг рекурсивного поиска файлов.\nПо умолчанию: True, поиск файлов по вложенным папкам",
    show_default=True,
    required=False,
    default=True)
@option(
    "--keep-logs",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг сохранения директории с лог-файлом по завершении \nработы в штатном режиме.\n"
         "По умолчанию: False, лог-файл и директория удаляются",
    show_default=True,
    required=False,
    default=False)
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
@pass_context
def repair_svg_command(
        ctx: Context,
        files: Iterable[StrPath] = None,
        directory: StrPath = None,
        recursive: bool = True,
        keep_logs: bool = False):
    files: list[StrPath] | None = get_files(files, directory, recursive)

    if files is None:
        pause(PRESS_ENTER_KEY)
        ctx.exit(0)

    FOREIGN_OBJECT: str = "<foreignObject.*?</foreignObject>"
    TEXT: str = (
        r"<a\s?transform=\"translate(0,-5)\"\s?xlink:href=\"https://www.drawio.com/doc/faq/svg-export-text-problems"
        "\".*?</a>")
    FEATURES: str = r"<g>\s?<g\s?requiredFeatures=\"http://www.w3.org/TR/SVG11/feature#Extensibility\"/>\s?</g>"

    for file in files:
        file: Path = Path(file).expanduser().resolve()

        if not file.exists(follow_symlinks=True):
            echo(f"Указан не существующий файл {file}")
            continue

        elif not file.is_file():
            echo(f"Путь {file} указывает не на файл")
            continue

        elif file.suffix != ".svg":
            echo(f"Указанный файл {file.name} имеет расширение не SVG")
            continue

        else:
            try:
                with open(file, "rb") as fr:
                    svg: str = fr.read().decode()

                svg: str = sub(TEXT, "", svg, flags=DOTALL | MULTILINE)
                svg: str = sub(FOREIGN_OBJECT, "", svg, flags=DOTALL | MULTILINE)
                svg: str = sub(FEATURES, "", svg, flags=DOTALL | MULTILINE)
                svg: str = svg.replace("switch>", "g>")

                with open(file, "wb") as fw:
                    fw.write(svg.encode())

                logger.info(f"Файл {file.name} успешно обработан")

            except PermissionError:
                logger.error(f"Недостаточно прав для чтения/записи в файл {file.name}")
                continue

            except RuntimeError:
                logger.error(f"Истекло время чтения/записи файл {file.name}")
                continue

            except OSError as e:
                logger.error(f"Ошибка {e.__class__.__name__}: {e.strerror}")
                continue

    ctx.obj["keep_logs"] = keep_logs
    pause(PRESS_ENTER_KEY)
    ctx.invoke(clear_logs)
