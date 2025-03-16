# -*- coding: utf-8 -*-
from collections.abc import Iterable
from os import scandir, sep
from pathlib import Path
from sys import platform

from click import pause
from click.core import Context
from click.decorators import argument, help_option, option, pass_context
from click.types import BOOL, Path as ClickPath, STRING
from click.utils import echo
from loguru import logger

from utilities.common.shared import HELP, PRESS_ENTER_KEY, pretty_print, StrPath
from utilities.scripts.cli import clear_logs, cli, MutuallyExclusiveOption, SwitchArgsAPIGroup


def check_content_common(path: Path):
    parts: tuple[str, ...] = path.parts

    for index, part in enumerate(parts[:-1]):
        if part == "content" and parts[index + 1] == "common":
            return index

    else:
        return -1


def generate_base_root(path: Path, content_common_index: int):
    parts: list[str] = [*path.parts]
    echo(f"{parts=}")
    # return Path(sep.join(parts[:content_common_index])).relative_to(path).as_posix()

    if content_common_index == -1:
        return path

    else:
        if not platform.startswith("win"):
            parts[0] = ""

        # return Path(sep.join(parts[:content_common_index])).relative_to(path).as_posix()
        # path.root.joinpath("/".join(parts[1:content_common_index])).relative_to(path)
        return path.relative_to(Path().joinpath("/".join(parts[:content_common_index]))).as_posix()


def check_path(
        path: StrPath,
        ignored_dirs: Iterable[str],
        ignored_files: Iterable[str],
        extensions: Iterable[str],
        language: str | None):
    path: Path = Path(path)

    is_dir: bool = path.is_dir()
    is_in_ignored_dirs: bool = any(part in ignored_dirs for part in path.parts)
    has_ignored_name: bool = path.name in ignored_dirs
    is_in_ignored_files: bool = path.stem in ignored_files
    has_ignored_extension: bool = path.suffix not in extensions if extensions else False

    if language is None:
        has_ignored_language: bool = False

    elif not language:
        has_ignored_language: bool = len(path.suffixes) == 1

    else:
        has_ignored_language: bool = f".{language}" not in path.suffixes

    conditions: list[bool] = [
        is_dir, is_in_ignored_dirs, has_ignored_name, is_in_ignored_files, has_ignored_extension, has_ignored_language]

    logger.debug(
        f"Проверка пути {path}:"
        f"\nis_dir = {is_dir}"
        f"\nis_in_ignored_dirs = {is_in_ignored_dirs}"
        f"\nhas_ignored_name = {has_ignored_name}"
        f"\nis_in_ignored_files = {is_in_ignored_files}"
        f"\nhas_ignored_extension = {has_ignored_extension}"
        f"\nhas_ignored_language = {has_ignored_language}\n")

    return not any(conditions)


def walk_full(
        path: StrPath,
        ignored_dirs: Iterable[str],
        ignored_files: Iterable[str],
        extensions: Iterable[str],
        language: str | None,
        results: list[Path] = None):
    if results is None:
        results: list[Path] = []

    for element in scandir(path):
        item: Path = Path(element.path)

        if element.is_dir(follow_symlinks=True):
            walk_full(item, ignored_dirs, ignored_files, extensions, language, results)

        elif check_path(item, ignored_dirs, ignored_files, extensions, language):
            results.append(item.relative_to(path))

        else:
            continue

    return results


@cli.command(
    "list-files",
    cls=SwitchArgsAPIGroup,
    help="Команда для вывода файлов в директории")
@argument(
    "root_dir",
    type=ClickPath(
        file_okay=False,
        resolve_path=True,
        path_type=Path,
        dir_okay=True),
    required=True,
    metavar="ROOT_DIR")
@option(
    "-d", "--ignored-dirs", "ignored_dirs",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["all_dirs"],
    type=STRING,
    help="\b\nПеречень игнорируемых директорий. Может использоваться \nнесколько раз."
         "\nПо умолчанию: _temp_folder, _temp_storage, private",
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
    help="\b\nПеречень игнорируемых файлов. Может использоваться"
         "\nнесколько раз."
         "\nПо умолчанию: README, _check_list",
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
    help="\b\nФлаг обработки всех файлов."
         "\nПо умолчанию: False, выводятся файлы только"
         "\nс определенными именами",
    multiple=False,
    required=False,
    show_default=True,
    default=False)
@option(
    "-e", "--extensions", "extensions",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["all_extensions"],
    type=STRING,
    help="\b\nОбрабатываемые типы файлов, разделяемые пробелом."
         "\nПо умолчанию: md adoc",
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
    help="\b\nФлаг обработки файлов всех расширений."
         "\nПо умолчанию: False, выводятся файлы только"
         "\nс определенными расширениями",
    multiple=False,
    required=False,
    show_default=True,
    default=False)
@option(
    "-l", "--language", "language",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["all_languages"],
    type=STRING,
    help="\b\nЯзык файлов.\nПо умолчанию: \"\", выводятся файлы на всех языках",
    multiple=False,
    required=False,
    metavar="LANG",
    show_default=True,
    default=None)
@option(
    "--all-langs", "all_languages",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["language"],
    type=BOOL,
    help="\b\nФлаг обработки файлов всех языков."
         "\nПо умолчанию: True, выводятся файлы на всех языках",
    multiple=False,
    required=False,
    show_default=True,
    default=True)
@option(
    "-i/-I", "--ignore-index/--keep-index", "ignore_index",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг игнорирования файлов _index любого расширения."
         "\nПо умолчанию: False, файл включается в список",
    show_default=True,
    required=False,
    default=False)
@option(
    "-p", "--prefix", "prefix",
    type=STRING,
    help="\b\nПрефикс, добавляемый к названиям файлов."
         "\nПо умолчанию: если в пути есть 'content' и 'common',"
         "\nто путь, пригодный для добавления в YAML-файл для PDF;"
         "\nиначе -- ''."
         "\nПримечание. Если задано --no-prefix, то игнорируется",
    multiple=False,
    required=False,
    metavar="PFX",
    show_default=True,
    default=None)
@option(
    "-n/-N", "--no-prefix/--with-prefix", "no_prefix",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг вывода исключительно относительных путей до файлов"
         "\nбез префиксов."
         "\nПо умолчанию: False, префикс задается опцией --prefix."
         "\nПримечание. Имеет приоритет над опцией --prefix",
    show_default=True,
    required=False,
    default=False)
@option(
    "-H", "--hidden",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг поиска скрытых файлов."
         "\nПо умолчанию: False, скрытые файлы игнорируются",
    show_default=True,
    required=False,
    default=False)
@option(
    "-r/-R", "--recursive/--no-recursive",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг рекурсивного поиска файлов."
         "\nПо умолчанию: True, вложенные файлы учитываются",
    show_default=True,
    required=False,
    default=True)
@option(
    "-k/-K", "--keep-logs/--remove-logs",
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
def list_files_command(
        ctx: Context,
        root_dir: StrPath,
        ignored_dirs: Iterable[str] = None,
        all_dirs: bool = False,
        ignored_files: Iterable[str] = None,
        all_files: bool = False,
        extensions: str = None,
        all_extensions: bool = False,
        language: str = None,
        all_languages: bool = True,
        prefix: str = None,
        no_prefix: bool = False,
        hidden: bool = False,
        ignore_index: bool = False,
        recursive: bool = True,
        auxiliary: bool = False,
        keep_logs: bool = False):
    root_dir: Path = root_dir.expanduser()

    if extensions is None and not all_extensions:
        extensions: set[str] = {".md", ".adoc"}

    elif extensions is None:
        extensions: set[str] = set()

    elif not all_extensions:
        extensions: set[str] = {
            f".{extension.removeprefix('.')}"
            for extension in extensions.strip().split(" ")}

    else:
        extensions: set[str] = set()

    if ignored_files is None and all_files is None:
        ignored_files: set[str] = {"README", "_check_list"}

    elif ignored_files is None or not ignored_files or ignored_files == [""]:
        ignored_files: set[str] = set()

    elif all_files is None and all_files is False:
        ignored_files: set[str] = {
            ignored_file.split(".")[-1] for ignored_file in ignored_files}

    else:
        ignored_files: set[str] = set()

    if ignore_index:
        ignored_files.add("_index")

    if ignored_dirs is None and all_dirs is None:
        ignored_dirs: set[str] = {"_temp_folder", "private", "_temp_storage"}

    elif ignored_dirs is None or not ignored_dirs or ignored_dirs == [""]:
        ignored_dirs: set[str] = set()

    elif all_dirs is None and all_dirs is False:
        ignored_dirs: set[str] = set(ignored_dirs)

    else:
        ignored_dirs: set[str] = set()

    if language is None:
        language: str | None = None

    elif language.lower() == "ru" or all_languages is True:
        language: str | None = ""

    else:
        language: str | None = language.lower()

    content_common_index: int = check_content_common(root_dir)

    if no_prefix:
        prefix: str = ""

    elif prefix is None:
        if content_common_index > 0:
            prefix: str = f"- {generate_base_root(root_dir, content_common_index)}/"

        else:
            prefix: str = ""

    logger.debug(
        f"ignored_dirs = {ignored_dirs}"
        f"\nall_dirs = {all_dirs}"
        f"\nignored_files = {ignored_files}"
        f"\nall_files = {all_files}"
        f"\nextensions = {extensions}"
        f"\nall_extensions = {all_extensions}"
        f"\nlanguage = {language}"
        f"\nall_languages = {all_languages}"
        f"\nprefix = {prefix}"
        f"\nno_prefix = {no_prefix}"
        f"\nhidden = {hidden}"
        f"\nignore_index = {ignore_index}"
        f"\nrecursive = {recursive}"
        f"\nauxiliary = {auxiliary}"
        f"\nkeep_logs = {keep_logs}")

    results: list[Path] = walk_full(root_dir, ignored_dirs, ignored_files, extensions, language)

    if not auxiliary:
        echo(pretty_print(results))
        ctx.obj["keep_logs"] = keep_logs
        ctx.invoke(clear_logs)

    else:
        return results


def get_files(
        ctx: Context, *,
        files: Iterable[StrPath] = None,
        directory: StrPath = None,
        recursive: bool = True,
        language: str | None = None,
        extensions: str = "md adoc"):
    if files is None and directory is None:
        logger.error("Хотя бы один из параметров --file, --dir должен быть задан")
        pause(PRESS_ENTER_KEY)

    if files is None:
        files: list[StrPath] = []

    else:
        files: list[StrPath] = [*files]

    if directory is not None:
        directory: Path = Path(directory).expanduser()

        if language is None:
            all_languages: bool = False

        else:
            all_languages: bool = not bool(language)

        listed_files: list[str] = ctx.invoke(
            list_files_command,
            root_dir=directory,
            all_dirs=True,
            all_languages=all_languages,
            language=language,
            extensions=extensions,
            prefix="",
            hidden=False,
            recursive=recursive,
            auxiliary=True)

        files.extend(map(directory.joinpath, listed_files))

    logger.debug(f"Обрабатываемые файлы:\n{pretty_print(files)}")

    return files
