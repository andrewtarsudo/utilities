# -*- coding: utf-8 -*-
from collections.abc import Iterable
from glob import iglob
from pathlib import Path

from click.core import Context
from click.decorators import argument, help_option, option, pass_context
from click.types import BOOL, Path as ClickPath, STRING
from click.utils import echo

from utilities.common.constants import HELP, StrPath
from utilities.scripts.cli import APIGroup, clear_logs, command_line_interface, MutuallyExclusiveOption


def generate_prefix(path: Path):
    try:
        parts: tuple[str, ...] = path.parts
        return "- content/common/" if (parts[-2], parts[-1]) == ("content", "common") else ""

    except IndexError or KeyError:
        return ""


@command_line_interface.command(
    "list-files",
    cls=APIGroup,
    help="Команда для вывода файлов в директории")
@argument(
    "root_dir",
    type=ClickPath(
        file_okay=False,
        resolve_path=True,
        path_type=Path,
        dir_okay=True),
    default=Path.cwd(),
    required=True,
    metavar="ROOT_DIR")
@option(
    "-d", "--ignored-dirs", "ignored_dirs",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["all_dirs"],
    type=STRING,
    help="\b\nПеречень игнорируемых директорий. Может использоваться \nнесколько раз.\nПо умолчанию: _temp_folder, "
         "_temp_storage, private",
    multiple=True,
    required=False,
    metavar="DIR ... DIR",
    show_default=True,
    default=["_temp_folder", "_temp_storage", "private"])
@option(
    "--all-dirs", "all_dirs",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["ignored_dirs"],
    type=BOOL,
    help="\b\nФлаг обработки всех директорий. По умолчанию: False",
    multiple=False,
    required=False,
    show_default=True,
    default=False)
@option(
    "-f", "--ignored-files", "ignored_files",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["all_files"],
    type=STRING,
    help="\b\nПеречень игнорируемых файлов. Может использоваться несколько \nраз.\nПо умолчанию: README, _check_list",
    multiple=True,
    required=False,
    metavar="FILE ... FILE",
    show_default=True,
    default=["README", "_check_list"])
@option(
    "--all-files", "all_files",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["ignored_files"],
    type=BOOL,
    help="\b\nФлаг обработки всех файлов.\nПо умолчанию: False, выводятся файлы с определенными именами",
    multiple=False,
    required=False,
    show_default=True,
    default=False)
@option(
    "-e", "--extensions", "extensions",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["all_extensions"],
    type=STRING,
    help="\b\nОбрабатываемые типы файлов, разделяемые пробелом.\nПо умолчанию: md adoc",
    multiple=False,
    required=False,
    metavar="\"EXT ... EXT\"",
    show_default=True,
    default="md adoc")
@option(
    "--all-ext", "all_extensions",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["extensions"],
    type=BOOL,
    help="\b\nФлаг обработки файлов всех расширений.\nПо умолчанию: False, вывод файлов определенных расширений",
    multiple=False,
    required=False,
    show_default=True,
    default=False)
@option(
    "-l", "--language", "language",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["all_languages"],
    type=STRING,
    help="\b\nЯзык файлов.\nПо умолчанию: \"\", вывод всех файлов независимо от языка",
    multiple=False,
    required=False,
    metavar="LANG",
    show_default=True,
    default="")
@option(
    "--all-langs", "all_languages",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["language"],
    type=BOOL,
    help="\b\nФлаг обработки файлов всех языков.\nПо умолчанию: True, вывод файлов на всех языках",
    multiple=False,
    required=False,
    show_default=True,
    default=True)
@option(
    "-p", "--prefix", "prefix",
    cls=MutuallyExclusiveOption,
    type=STRING,
    help="\b\nПрефикс, добавляемый к названиям файлов.\nПо умолчанию: '- content/common/'",
    multiple=False,
    required=False,
    metavar="PFX",
    show_default=True,
    default=None)
@option(
    "--hidden",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг поиска скрытых файлов.\nПо умолчанию: False, исключение скрытых файлов из вывода",
    show_default=True,
    required=False,
    default=False)
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
def list_files_command(
        ctx: Context,
        root_dir: StrPath,
        ignored_dirs: Iterable[str] = None,
        all_dirs: bool = False,
        ignored_files: Iterable[str] = None,
        all_files: bool = False,
        extensions: str = "md adoc",
        all_extensions: bool = False,
        language: str = "",
        all_languages: bool = True,
        prefix: str = "- content/common/",
        hidden: bool = False,
        recursive: bool = True,
        auxiliary: bool = False,
        keep_logs: bool = False):
    root_dir: Path = Path(root_dir).expanduser()

    if extensions is None and all_extensions is None:
        extensions: list[str] = [".md", ".adoc"]

    elif extensions is None:
        extensions: list[str] = []

    elif all_extensions is None:
        extensions: list[str] = [
            f".{extension.removeprefix('.')}"
            for extension in extensions.strip().split(" ")]

    else:
        extensions: list[str] = []

    if ignored_files is None and all_files is None:
        ignored_files: list[str] = ["README", "_check_list"]

    elif ignored_files is None or not ignored_files or ignored_files == [""]:
        ignored_files: list[str] = []

    elif all_files is None and all_files is False:
        ignored_files: list[str] = [
            ignored_file.split(".")[-1] for ignored_file in ignored_files]

    else:
        ignored_files: list[str] = []

    if ignored_dirs is None and all_dirs is None:
        ignored_dirs: list[str] = ["_temp_folder", "private", "_temp_storage"]

    elif ignored_dirs is None or not ignored_dirs or ignored_dirs == [""]:
        ignored_dirs: list[str] = []

    elif all_dirs is None and all_dirs is False:
        ignored_dirs: list[str] = [*ignored_dirs]

    else:
        ignored_dirs: list[str] = []

    if language is None or language.lower() == "ru" or all_languages is True:
        language: str = ""

    else:
        language: str = language.lower()

    if prefix is None:
        prefix: str = generate_prefix(root_dir)

    results: list[str] = []

    for item in iglob(
            "**",
            root_dir=root_dir,
            recursive=recursive,
            include_hidden=hidden):
        _: Path = root_dir.joinpath(item)

        if _.is_dir():
            continue

        elif any(part in ignored_dirs for part in _.parts) or _.name in ignored_dirs:
            continue

        elif _.stem in ignored_files:
            continue

        elif extensions != [] and _.suffix not in extensions:
            continue

        elif language and not _.stem.endswith(language):
            continue

        elif not language and len(_.suffixes) > 1:
            continue

        else:
            results.append(f"{prefix}{Path(item).as_posix()}")

    if not auxiliary:
        echo("\n".join(results))
        ctx.obj["keep_logs"] = keep_logs
        ctx.invoke(clear_logs)

    else:
        return results
