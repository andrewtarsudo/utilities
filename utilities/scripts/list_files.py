# -*- coding: utf-8 -*-
from collections.abc import Iterable
from glob import iglob
from pathlib import Path

from click.core import Context
from click.termui import pause
from loguru import logger
from rich import print
from typer.main import Typer
from typer.params import Argument, Option
from typing_extensions import Annotated, List

from utilities.common.constants import PRESS_ENTER_KEY, pretty_print, StrPath
from utilities.common.functions import clear_logs

list_files: Typer = Typer(
    add_help_option=True,
    rich_markup_mode="rich",
    help="Команда для вывода файлов в директории")


def check_content_common(path: Path):
    parts: tuple[str, ...] = path.parts

    for index, part in enumerate(parts[:-1]):
        if part == "content" and parts[index + 1] == "common":
            return index

    else:
        return -1


def generate_base_root(path: Path, content_common_index: int):
    parts: tuple[str, ...] = path.parts

    if content_common_index == -1:
        return path

    else:
        return path.relative_to(Path().joinpath("/".join(parts[:content_common_index]))).as_posix()


def check_path(
        path: Path,
        ignored_dirs: Iterable[str],
        ignored_files: Iterable[str],
        extensions: Iterable[str],
        language: str | None):
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
        is_dir, is_in_ignored_dirs, has_ignored_name, is_in_ignored_files, has_ignored_extension, has_ignored_language
    ]

    logger.debug(
        f"Проверка пути {path}:"
        f"\nis_dir = {is_dir}"
        f"\nis_in_ignored_dirs = {is_in_ignored_dirs}"
        f"\nhas_ignored_name = {has_ignored_name}"
        f"\nis_in_ignored_files = {is_in_ignored_files}"
        f"\nhas_ignored_extension = {has_ignored_extension}"
        f"\nhas_ignored_language = {has_ignored_language}")

    return not any(conditions)


@list_files.command(
    name="list-files",
    help="Команда для вывода файлов в директории")
def list_files_command(
        ctx: Context,
        root_dir: Annotated[
            Path,
            Argument(
                metavar="ROOT_DIR",
                exists=True,
                dir_okay=True,
                file_okay=False,
                allow_dash=False,
                resolve_path=True)],
        ignored_dirs: Annotated[
            List[Path],
            Option(
                "-d", "--ignored-dirs",
                file_okay=False,
                dir_okay=True,
                exists=True,
                allow_dash=False,
                show_default=True,
                metavar="DIR ... DIR",
                resolve_path=True,
                help="Перечень игнорируемых директорий. Может использоваться \nнесколько раз."
                     "\nПо умолчанию: _temp_folder, _temp_storage, private")] = None,
        all_dirs: Annotated[
            bool,
            Option(
                "--all-dirs",
                show_default=True,
                help="Флаг обработки всех директорий. По умолчанию: False")] = False,
        ignored_files: Annotated[
            List[Path],
            Option(
                "-d", "--ignored-dirs",
                file_okay=True,
                dir_okay=False,
                exists=True,
                allow_dash=False,
                show_default=True,
                metavar="FILE ... FILE",
                resolve_path=True,
                help="Перечень игнорируемых файлов. Может использоваться"
                     "\nнесколько раз."
                     "\nПо умолчанию: README, _check_list")] = None,
        all_files: Annotated[
            bool,
            Option(
                "--all-langs",
                show_default=True,
                help="Флаг обработки файлов всех языков."
                     "\nПо умолчанию: True, выводятся файлы на всех языках")] = False,
        extensions: Annotated[
            str,
            Option(
                "-e", "--extensions",
                help="Обрабатываемые типы файлов, разделяемые пробелом."
                     "\nПо умолчанию: md adoc",
                metavar="\"EXT ... EXT\"",
                show_default=True)] = None,
        all_extensions: Annotated[
            bool,
            Option(
                "--all-ext",
                show_default=True,
                help="Флаг обработки файлов всех расширений."
                     "\nПо умолчанию: False, выводятся файлы только"
                     "\nс определенными расширениями")] = False,
        language: Annotated[
            str,
            Option(
                "-l", "--language",
                help="Язык файлов.\nПо умолчанию: \"\", выводятся файлы на всех языках",
                metavar="LANGUAGE",
                show_default=True)] = None,
        all_languages: Annotated[
            bool,
            Option(
                "--all-langs",
                show_default=True,
                help="Флаг обработки файлов всех языков."
                     "\nПо умолчанию: True, выводятся файлы на всех языках")] = True,
        prefix: Annotated[
            str,
            Option(
                "-p", "--prefix",
                help="Префикс, добавляемый к названиям файлов."
                     "\nПо умолчанию: если в пути есть 'content' и 'common',"
                     "\nто путь, пригодный для добавления в YAML-файл для PDF;"
                     "\nиначе -- ''."
                     "\nПримечание. Если задано --no-prefix, то игнорируется",
                metavar="PFX",
                show_default=True)] = None,
        no_prefix: Annotated[
            bool,
            Option(
                "-n", "--no-prefix",
                show_default=True,
                help="Флаг вывода исключительно относительных путей до файлов"
                     "\nбез префиксов."
                     "\nПо умолчанию: False, префикс задается опцией --prefix."
                     "\nПримечание. Имеет приоритет над опцией --prefix", )] = False,
        hidden: Annotated[
            bool,
            Option(
                "-H/ ", "--hidden/--no-hidden",
                show_default=True,
                help="Флаг поиска скрытых файлов."
                     "\nПо умолчанию: False, скрытые файлы игнорируются")] = False,
        ignore_index: Annotated[
            bool,
            Option(
                "-i/-I", "--ignore-index/--no-ignore-index",
                show_default=True,
                help="Флаг игнорирования файлов _index любого расширения."
                     "\nПо умолчанию: False, файл включается в список")] = False,
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
                     "\nПо умолчанию: False, лог-файл и директория удаляются")] = False,
        auxiliary: bool = False):
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
        ignored_dirs: set[Path] = set(ignored_dirs)

    else:
        ignored_dirs: set[Path] = set()

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

    results: list[str] = []

    for item in iglob(
            "**/*",
            root_dir=root_dir,
            recursive=recursive,
            include_hidden=hidden):
        _: Path = root_dir.joinpath(item)

        logger.debug(f"Файл {item}")

        if check_path(_, ignored_dirs, ignored_files, extensions, language):
            results.append(f"{prefix}{Path(item).as_posix()}")

    if not auxiliary:
        print(pretty_print(results))
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
