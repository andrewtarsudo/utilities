# -*- coding: utf-8 -*-
from pathlib import Path
from re import DOTALL, MULTILINE, sub
from typing import Iterable

from click.core import Context
from click.decorators import help_option, option, pass_context
from click.types import BOOL, Path as ClickPath
from click.utils import echo
from loguru import logger

from utilities.common.config_file import config_file
from utilities.common.shared import HELP, StrPath
from utilities.scripts.api_group import APIGroup
from utilities.scripts.cli import cli
from utilities.common.completion import dir_completion, file_completion
from utilities.scripts.list_files import get_files


@cli.command(
    "repair-svg",
    cls=APIGroup,
    help="Команда для исправления файлов SVG")
@option(
    "-f", "--file", "files",
    type=ClickPath(
        file_okay=True,
        readable=True,
        resolve_path=True,
        allow_dash=False,
        dir_okay=False),
    help="\b\nФайл для обработки. Может использоваться несколько раз",
    multiple=True,
    required=False,
    metavar="FILE ... FILE",
    shell_complete=file_completion,
    default=config_file.get_commands("repair-svg", "files"))
@option(
    "-d", "--dir", "directory",
    type=ClickPath(
        file_okay=False,
        resolve_path=True,
        allow_dash=False,
        dir_okay=True),
    help="Директория для обработки",
    multiple=False,
    required=False,
    metavar="DIR",
    shell_complete=dir_completion,
    default=config_file.get_commands("repair-svg", "directory"))
@option(
    "-r/-R", "--recursive/--no-recursive",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг рекурсивного поиска файлов."
         "\nПо умолчанию: True, вложенные файлы учитываются",
    show_default=True,
    required=False,
    default=config_file.get_commands("repair-svg", "recursive"))
@option(
    "-k/-K", "--keep-logs/--remove-logs",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг сохранения директории с лог-файлом по завершении"
         "\nработы в штатном режиме."
         "\nПо умолчанию: False, лог-файл и директория удаляются",
    show_default=True,
    required=False,
    default=config_file.get_commands("repair-svg", "keep_logs"))
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
    files: list[StrPath] | None = get_files(
        ctx,
        files=files,
        directory=directory,
        recursive=recursive,
        extensions="svg")

    if files is not None and files:
        FOREIGN_OBJECT: str = "<foreignObject.*?</foreignObject>"
        TEXT: str = (
            r"<a\s?transform=\"translate(0,-5)\"\s?xlink:href=\"https://www.drawio.com/doc/faq/svg-export-text-problems"
            "\".*?</a>")
        FEATURES: str = r"<g>\s?<g\s?requiredFeatures=\"http://www.w3.org/TR/SVG11/feature#Extensibility\"/>\s?</g>"

        for file in files:
            file: Path = Path(file).expanduser().resolve()

            logger.debug(f"Файл {file}")

            if not file.exists():
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
