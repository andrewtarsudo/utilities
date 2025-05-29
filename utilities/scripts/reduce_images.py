# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Iterable

from click.core import Context
from click.decorators import help_option, option, pass_context
from click.types import BOOL, Path as ClickPath
from loguru import logger
from PIL import Image

from utilities import echo
from utilities.common.config_file import config_file
from utilities.common.shared import HELP, separator, StrPath
from utilities.scripts.api_group import APIGroup, ConditionalOption
from utilities.scripts.cli import cli
from utilities.common.completion import dir_completion, file_completion
from utilities.scripts.list_files import get_files


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


@cli.command(
    "reduce-images",
    cls=APIGroup,
    help="Команда для уменьшения веса изображений JPG, PNG")
@option(
    "-f", "--file", "files",
    type=ClickPath(
        file_okay=True,
        readable=True,
        resolve_path=True,
        allow_dash=False,
        dir_okay=False),
    cls=ConditionalOption,
    conditional=["directory"],
    help="\b\nФайл для обработки. Может использоваться несколько раз",
    multiple=True,
    required=False,
    metavar="FILE ... FILE",
    shell_complete=file_completion,
    default=config_file.get_commands("reduce-images", "files"))
@option(
    "-d", "--dir", "directory",
    type=ClickPath(
        file_okay=False,
        resolve_path=True,
        allow_dash=False,
        dir_okay=True),
    cls=ConditionalOption,
    conditional=["files"],
    help="Директория для обработки",
    multiple=False,
    required=False,
    metavar="DIR",
    shell_complete=dir_completion,
    default=config_file.get_commands("reduce-images", "directory"))
@option(
    "--dry-run/--no-dry-run",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг вывода изменений размеров файлов без их изменения.\n"
         "По умолчанию: False, файлы перезаписываются",
    show_default=True,
    required=False,
    default=config_file.get_commands("reduce-images", "dry_run"))
@option(
    "-r/-R", "--recursive/--no-recursive",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг рекурсивного поиска файлов."
         "\nПо умолчанию: True, вложенные файлы учитываются",
    show_default=True,
    required=False,
    default=config_file.get_commands("reduce-images", "recursive"))
@option(
    "-k/-K", "--keep-logs/--remove-logs",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг сохранения директории с лог-файлом по завершении"
         "\nработы в штатном режиме."
         "\nПо умолчанию: False, лог-файл и директория удаляются",
    show_default=True,
    required=False,
    default=config_file.get_commands("reduce-images", "keep_logs"))
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
@pass_context
def reduce_images_command(
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

            current_size: int = file.stat(follow_symlinks=True).st_size
            before += current_size

            result: Path = duplicate_image(file, dry_run)
            new_size: int = result.stat(follow_symlinks=True).st_size

            after += new_size
            logger.info(f"Файл {file.name}: {file_size(current_size)} -> {file_size(new_size)}")

            if result.stem.startswith("temp_file"):
                result.unlink(missing_ok=True)

        echo(separator)
        echo(f"Итоговое изменение: {file_size(before)} -> {file_size(after)}")

    if dry_run:
        echo("Файлы не были изменены, поскольку использована опция --dry-run")

    ctx.obj["keep_logs"] = keep_logs
