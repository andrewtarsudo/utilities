# -*- coding: utf-8 -*-
from pathlib import Path
from re import finditer

from click.core import Context
from click.decorators import argument, help_option, option, pass_context
from click.types import BOOL, Path as ClickPath
from loguru import logger

from utilities.common.config_file import config_file
from utilities.common.functions import file_reader, file_writer, pretty_print
from utilities.common.shared import HELP, INDEX_STEMS, StrPath
from utilities.scripts.api_group import SwitchArgsAPIGroup
from utilities.scripts.cli import cli
from utilities.common.completion import dir_completion
from utilities.scripts.list_files import get_files


class File:
    pattern: str = None

    def __init__(self, path: StrPath):
        self._path: Path = Path(path).resolve()
        self._content: list[str] = file_reader(self._path, "lines", encoding="utf-8")

    def __iter__(self):
        return iter(self._content)

    def __bool__(self):
        return self._path.stem in INDEX_STEMS

    @property
    def full_links(self) -> list[Path]:
        return []

    def fix_link(self, link: str):
        return Path(link).resolve() if bool(self) else Path(link.removeprefix("../"))


class MdFile(File):
    pattern: str = r"!\[.*?\]\((.+?)\)"

    @property
    def full_links(self):
        return [
            self.fix_link(m.group(1))
            for line in iter(self)
            for m in finditer(self.__class__.pattern, line)]


class AsciiDocFile(File):
    pattern: str = r"image:+(.+?)\[.*?\]"

    @property
    def imagesdir(self):
        for line in iter(self):
            if line.startswith("ifndef::imagesdir") and ":imagesdir:" in (
                    line_shorten := line.removeprefix("ifndef::imagesdir")):
                imagesdir: str = line_shorten.removeprefix("[:imagesdir:").strip().removesuffix("]")
                return self._path.parent.joinpath(imagesdir).resolve()

        else:
            return Path(self._path.parent).resolve()

    @property
    def full_links(self):
        return [
            self.imagesdir.joinpath(m.group(1)).resolve()
            for line in iter(self)
            for m in finditer(self.__class__.pattern, line)]


@cli.command(
    "filter-images",
    cls=SwitchArgsAPIGroup,
    help="Команда для удаления неиспользуемых изображений")
@argument(
    "root",
    type=ClickPath(
        file_okay=False,
        resolve_path=True,
        allow_dash=False,
        dir_okay=True),
    required=True,
    shell_complete=dir_completion,
    metavar="ROOT")
@option(
    "-d/-D", "--dry-run/--no-dry-run",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг вывода некорректных ссылок на экран без изменения"
         "\nфайлов."
         "\nПо умолчанию: False, файлы удаляются",
    show_default=True,
    required=False,
    default=config_file.get_commands("filter-images", "dry_run"))
@option(
    "-o", "--output", "output",
    type=ClickPath(
        file_okay=True,
        readable=True,
        resolve_path=True,
        allow_dash=True,
        dir_okay=False),
    help="\b\nФайл для записи вывода."
         "\nПо умолчанию: вывод в консоль",
    multiple=False,
    required=False,
    metavar="FILE",
    default=config_file.get_commands("filter-images", "output"))
@option(
    "-r/-R", "--recursive/--no-recursive",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг рекурсивного поиска файлов."
         "\nПо умолчанию: True, вложенные файлы учитываются",
    show_default=True,
    required=False,
    default=config_file.get_commands("filter-images", "recursive"))
@option(
    "-k/-K", "--keep-logs/--remove-logs",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг сохранения директории с лог-файлом по завершении"
         "\nработы в штатном режиме."
         "\nПо умолчанию: False, лог-файл и директория удаляются",
    show_default=True,
    required=False,
    default=config_file.get_commands("filter-images", "keep_logs"))
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
@pass_context
def filter_images_command(
        ctx: Context,
        root: StrPath,
        dry_run: bool = False,
        output: StrPath = None,
        recursive: bool = True,
        keep_logs: bool = False):
    messages: list[str] = []

    root: Path = Path(root)
    extensions: str = "png jpg jpeg bmp svg PNG JPG JPEG BMP SVG"

    images: list[StrPath] | None = get_files(
        ctx,
        directory=root,
        recursive=recursive,
        language=None,
        extensions=extensions)

    images_paths_names: dict[Path, str] = {
        root.joinpath(image): image.name for image in images}

    md_paths: list[StrPath] | None = get_files(
        ctx,
        directory=root,
        recursive=True,
        language=None,
        extensions="md")
    md_files: list[MdFile] = [MdFile(md_path) for md_path in md_paths]

    adoc_paths: list[StrPath] | None = get_files(
        ctx,
        directory=root,
        recursive=True,
        language=None,
        extensions="adoc")

    adoc_files: list[AsciiDocFile] = [AsciiDocFile(adoc_path) for adoc_path in adoc_paths]

    links_paths_names: dict[Path, str] = {
        Path(full_link).resolve(): full_link.name for file in [*md_files, *adoc_files] for full_link in file.full_links}

    def get_key_by_value(value, d: dict):
        for _, _v in d.items():
            if _v == value:
                return _

        else:
            return None

    for k, v in links_paths_names.items():
        images_paths_names.pop(k, None)
        images_paths_names.pop(get_key_by_value(v, images_paths_names), None)

    if images_paths_names:
        _: list[Path] = [unused_image.relative_to(root) for unused_image in images_paths_names]
        message: str = f"Неиспользуемые изображения:\n{pretty_print(_)}"

        messages.append(message)

        if output is not None:
            bool_convert: dict[bool, str] = {
                True: "Да",
                False: "Нет"}

            info: str = f"Директория {root}, рекурсивно: {bool_convert.get(recursive)}\n"
            file_writer(Path(output), pretty_print((info, message)))

            messages.append(f"\nФайл {output} записан")

        if not dry_run:
            for image in images_paths_names:
                image.unlink(missing_ok=True)

            messages.append("\nНеиспользуемые изображения удалены")

        else:
            messages.append("\nНеиспользуемые изображения не удалены, поскольку использована опция --dry-run")

    else:
        message: str = "\nНеиспользуемые изображения не найдены"
        messages.append(message)

    logger.info(pretty_print(messages))

    ctx.obj["keep_logs"] = keep_logs
