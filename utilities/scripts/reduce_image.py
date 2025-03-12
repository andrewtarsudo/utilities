# -*- coding: utf-8 -*-
from os.path import getsize
from pathlib import Path

from click.core import Context
from loguru import logger
from PIL import Image
from rich import print
from typer.main import Typer
from typer.params import Option
from typing_extensions import Annotated, List

from utilities.common.constants import separator, StrPath
from utilities.common.functions import clear_logs
from utilities.scripts.list_files import get_files

reduce_image: Typer = Typer(
    add_help_option=True,
    rich_markup_mode="rich",
    help="Команда для уменьшения размера изображений JPG, PNG")


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


@reduce_image.command(
    name="reduce-image",
    help="Команда для уменьшения размера изображений JPG, PNG")
def reduce_image_command(
        ctx: Context,
        files: Annotated[
            List[Path],
            Option(
                "--file", "-f",
                help="Файл для обработки. Может использоваться несколько раз",
                metavar="FILE ... FILE",
                exists=True,
                file_okay=True,
                dir_okay=False,
                resolve_path=True,
                allow_dash=False,
                rich_help_panel="Опции")] = None,
        directory: Annotated[
            Path,
            Option(
                "--dir", "-d",
                help="Директория для обработки",
                exists=True,
                file_okay=False,
                dir_okay=True,
                resolve_path=True,
                allow_dash=False,
                rich_help_panel="Опции")] = None,
        dry_run: Annotated[
            bool,
            Option(
                "-d/-D", "--dry-run/--no-dry-run",
                show_default=True,
                help="Флаг вывода изменений размеров файлов без их изменения."
                     "\nПо умолчанию: False, файлы перезаписываются",
                rich_help_panel="Опции")] = False,
        recursive: Annotated[
            bool,
            Option(
                "--recursive/--no-recursive", "-r/-R",
                show_default=True,
                help="Флаг рекурсивного поиска файлов.\nПо умолчанию: True, вложенные файлы учитываются",
                rich_help_panel="Опции")] = True,
        keep_logs: Annotated[
            bool,
            Option(
                "--keep-logs",
                show_default=True,
                help="Флаг сохранения директории с лог-файлом по завершении\nработы в штатном режиме."
                     "\nПо умолчанию: False, лог-файл и директория удаляются",
                rich_help_panel="Опции")] = False):
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

        print(separator)
        print(f"Итоговое изменение: {file_size(before)} -> {file_size(after)}")

    if dry_run:
        print("Файлы не были изменены, поскольку использована опция --dry-run")

    ctx.obj["keep_logs"] = keep_logs
    ctx.invoke(clear_logs)
