# -*- coding: utf-8 -*-
from os.path import getsize
from pathlib import Path
from typing import Iterable

from click.core import Context
from click.decorators import help_option, option, pass_context
from click.termui import echo
from click.types import BOOL, Path as ClickPath
from loguru import logger
from PIL import Image

from utilities.common.constants import HELP, separator, StrPath
from utilities.common.functions import get_files
from utilities.scripts.cli import APIGroup, clear_logs, command_line_interface


def file_size(value: int) -> str:
    if value <= 0:
        raise ValueError

    b: int = value
    kb: float = b / 1024

    if kb < 1:
        return f"{b} б"

    else:
        mb: float = kb / 1024

        if mb < 1:
            return f"{kb:.2f} Кб"

        else:
            return f"{mb:.2f} Мб"


def duplicate_image(file: StrPath, dry_run: bool = False) -> StrPath:
    if dry_run:
        destination: StrPath = file.with_stem("temp_file")

    else:
        destination: StrPath = file

    with Image.open(file, "r") as image:
        image.save(destination, optimize=True)

    return destination


@command_line_interface.command(
    "reduce-image",
    cls=APIGroup,
    help="Команда для уменьшения размера изображений JPG, PNG")
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
    default=None)
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
    default=None)
@option(
    "--dry-run",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг вывода изменений размеров файлов без их изменения.\n"
         "По умолчанию: False, файлы перезаписываются",
    show_default=True,
    required=False,
    default=False)
@option(
    "--recursive/--no-recursive",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг рекурсивного поиска файлов."
         "\nПо умолчанию: True, вложенные файлы учитываются",
    show_default=True,
    required=False,
    default=True)
@option(
    "--keep-logs",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг сохранения директории с лог-файлом по завершении"
         "\nработы в штатном режиме."
         "\nПо умолчанию: False, лог-файл и директория удаляются",
    show_default=True,
    required=False,
    default=False)
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
@pass_context
def reduce_image_command(
        ctx: Context,
        files: Iterable[StrPath] = None,
        directory: StrPath = None,
        recursive: bool = True,
        dry_run: bool = False,
        keep_logs: bool = False):
    extensions: str = "png jpg jpeg bmp"

    files: list[StrPath] | None = get_files(
        ctx,
        files=files,
        directory=directory,
        recursive=recursive,
        extensions=extensions)

    if files is not None and files:
        before: int = 0
        after: int = 0

        for file in files:
            file: Path = Path(file).expanduser().resolve()

            logger.debug(f"Файл {file}")

            current_size: int = getsize(file)
            before += current_size

            result: Path = duplicate_image(file, dry_run)
            new_size: int = getsize(result)

            after += new_size
            logger.info(f"Файл {file.name}: {file_size(current_size)} -> {file_size(new_size)}")

            if result.stem.startswith("temp_file"):
                result.unlink(missing_ok=True)

        echo(separator)
        echo(f"Итоговое изменение: {file_size(before)} -> {file_size(after)}")

    if dry_run:
        echo("Файлы не были изменены, поскольку использована опция --dry-run")

    ctx.obj["keep_logs"] = keep_logs
    ctx.invoke(clear_logs)
