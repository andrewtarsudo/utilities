# -*- coding: utf-8 -*-
from pathlib import Path
from re import DOTALL, MULTILINE, sub

from click.utils import echo
from loguru import logger
from typer.params import Option
from typer.main import Typer
from typer.models import Context
from typing_extensions import Annotated, List

from utilities.common.constants import StrPath
from utilities.common.functions import clear_logs
from utilities.scripts.list_files import get_files

repair_svg: Typer = Typer(
    add_help_option=True,
    rich_markup_mode="rich",
    help="Команда для исправления файлов SVG")


@repair_svg.command(
    name="repair-svg",
    help="Команда для исправления файлов SVG")
def repair_svg_command(
        ctx: Context,
        files: Annotated[
            List[Path],
            Option(
                "--file", "-f",
                help="Файл для обработки. Может использоваться несколько раз",
                metavar="FILE .. FILE",
                exists=True,
                file_okay=True,
                dir_okay=False,
                resolve_path=True,
                allow_dash=False)] = None,
        directory: Annotated[
            Path,
            Option(
                "--dir", "-d",
                help="Директория для обработки",
                exists=True,
                file_okay=False,
                dir_okay=True,
                resolve_path=True,
                allow_dash=False)] = None,
        recursive: Annotated[
            bool,
            Option(
                "--recursive/--no-recursive", "-r/-R",
                show_default=True,
                help="Флаг рекурсивного поиска файлов.\nПо умолчанию: True, вложенные файлы учитываются")] = True,
        keep_logs: Annotated[
            bool,
            Option(
                "--keep-logs",
                show_default=True,
                help="Флаг сохранения директории с лог-файлом по завершении\nработы в штатном режиме."
                     "\nПо умолчанию: False, лог-файл и директория удаляются")] = False):
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
    ctx.invoke(clear_logs)
