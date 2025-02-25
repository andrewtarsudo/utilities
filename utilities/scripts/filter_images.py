# -*- coding: utf-8 -*-
from pathlib import Path
from re import finditer, match, Match
from typing import Iterable

from click.core import Context
from click.decorators import argument, help_option, option, pass_context
from click.types import BOOL, Path as ClickPath
from loguru import logger

from utilities.common.constants import HELP, StrPath
from utilities.common.functions import file_reader, file_writer, get_files, pretty_print, ReaderMode
from utilities.scripts import command_line_interface
from utilities.scripts.cli import clear_logs, SwitchArgsAPIGroup


def flatten_iter(values: Iterable[Iterable[StrPath]]) -> list[StrPath]:
    return [_ for value in values for _ in value]


class File:
    pattern: str = None

    def __init__(self, path: StrPath):
        self._path: Path = Path(path).resolve()
        self._content: list[str] = file_reader(self._path, ReaderMode.LINES, encoding="utf-8")

    def __iter__(self):
        return iter(self._content)

    @property
    def is_index(self):
        return self._path.stem.removeprefix("_") == "index"

    @property
    def links(self) -> list[Path]:
        return []

    def fix_link(self, link: str):
        return Path(link) if self.is_index else Path(link.removeprefix("../"))


class MdFile(File):
    pattern = r"!\[.*?\]\((.+?)\)"

    @property
    def links(self):
        return [
            self.fix_link(m.group(1))
            for line in iter(self)
            for m in finditer(self.__class__.pattern, line)]


class AsciiDocFile(File):
    pattern = r"image::?(.+?)\[.*?\]"

    @property
    def imagesdir(self):
        for line in iter(self):
            m: Match = match(r"^.*:imagesdir:\s*([\w_/.-]+)", line)

            if m:
                return Path(m.group(1))

        else:
            return Path(self._path.parent)

    @property
    def links(self):
        return [
            self.imagesdir.joinpath(m.group(1))
            for line in iter(self)
            for m in finditer(self.__class__.pattern, line)]


@command_line_interface.command(
    "filter-images",
    cls=SwitchArgsAPIGroup,
    help="Команда для удаления неиспользуемых изображений")
@argument(
    "project_dir",
    type=ClickPath(
        file_okay=False,
        resolve_path=True,
        allow_dash=False,
        dir_okay=True),
    required=True,
    metavar="PROJECT_DIR")
@option(
    "-d", "--dry-run",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг вывода некорректных ссылок на экран без изменения"
         "\nфайлов."
         "\nПо умолчанию: False, файлы удаляются",
    show_default=True,
    required=False,
    default=False)
@option(
    "-o", "--output", "output",
    type=ClickPath(
        file_okay=True,
        readable=True,
        resolve_path=True,
        allow_dash=True,
        dir_okay=False),
    help="\b\nФайл для записи вывода. По умолчанию: вывод в консоль",
    multiple=False,
    required=False,
    metavar="FILE",
    default=None)
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
def filter_images_command(
        ctx: Context,
        project_dir: StrPath,
        dry_run: bool = False,
        output: StrPath = None,
        recursive: bool = True,
        keep_logs: bool = False):
    messages: list[str] = []

    extensions: str = "png jpg jpeg bmp"

    images: list[StrPath] | None = get_files(
        ctx,
        directory=project_dir,
        recursive=recursive,
        language=None,
        extensions=extensions)

    logger.debug(pretty_print(images))

    md_files: list[StrPath] | None = get_files(
        ctx,
        directory=project_dir,
        recursive=True,
        extensions="md")

    logger.debug(pretty_print(md_files))

    adoc_files: list[StrPath] | None = get_files(
        ctx,
        directory=project_dir,
        recursive=True,
        extensions="adoc")

    logger.debug(pretty_print(adoc_files))

    md_links: list[list[Path]] = [MdFile(md_path).links for md_path in md_files]
    adoc_links: list[list[Path]] = [AsciiDocFile(adoc_path).links for adoc_path in adoc_files]
    links: set[Path] = set(flatten_iter([*md_links, *adoc_links]))

    unused_images: set[Path] = set(images).difference(links)

    if unused_images:
        _: list[Path] = [unused_image.relative_to(project_dir) for unused_image in unused_images]
        message: str = f"Неиспользуемые изображения:\n{pretty_print(_)}"

        messages.append(message)

        if output is not None:
            bool_convert: dict[bool, str] = {
                True: "Да",
                False: "Нет"}

            info: str = f"Директория {project_dir}, рекурсивно: {bool_convert.get(recursive)}\n"
            file_writer(Path(output), pretty_print((info, message)))

            messages.append(f"\nФайл {output} записан")

        if not dry_run:
            for image in unused_images:
                image.unlink(missing_ok=True)

            messages.append("\nНеиспользуемые изображения удалены")

        else:
            messages.append("\nНеиспользуемые изображения не удалены, поскольку использована опция --dry-run")

    else:
        message: str = "\nНеиспользуемые изображения не найдены"
        messages.append(message)

    logger.info(pretty_print(messages))

    ctx.obj["keep_logs"] = keep_logs
    ctx.invoke(clear_logs)
