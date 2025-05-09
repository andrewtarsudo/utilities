# -*- coding: utf-8 -*-
from collections.abc import Iterable
from pathlib import Path

from click.core import Context
from click.decorators import argument, help_option, option, pass_context
from click.termui import pause
from click.types import BOOL, Path as ClickPath, STRING
from click.utils import echo
from loguru import logger

from utilities.common.config import config_file
from utilities.common.functions import is_windows, pretty_print, walk_full
from utilities.common.shared import ADOC_EXTENSION, HELP, MD_EXTENSION, PRESS_ENTER_KEY, StrPath
from utilities.scripts.api_group import MutuallyExclusiveOption, SwitchArgsAPIGroup
from utilities.scripts.cli import cli
from utilities.scripts.completion import dir_completion, file_completion


def check_content_common(path: Path):
    parts: tuple[str, ...] = path.parts

    for index, part in enumerate(parts[:-1]):
        if part == "content" and parts[index + 1] == "common":
            return index

    else:
        return -1


def generate_base_root(path: Path, content_common_index: int):
    parts: list[str] = [*path.parts]

    if content_common_index == -1:
        return path

    else:
        if not is_windows():
            parts[0] = ""

        return path.relative_to(Path().joinpath("/".join(parts[:content_common_index]))).as_posix()


def add_prefix(prefix: str, values: Iterable[StrPath] = None):
    if values is None:
        return []

    else:
        return [f"{prefix}{value}" for value in values]


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
    shell_complete=dir_completion,
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
    shell_complete=dir_completion,
    default=config_file.get_commands("list-files", "ignored_dirs"))
@option(
    "--all-dirs", "all_dirs",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["ignored_dirs"],
    type=BOOL,
    help="\b\nФлаг обработки всех директорий. По умолчанию: False",
    multiple=False,
    required=False,
    show_default=True,
    default=config_file.get_commands("list-files", "all_dirs"))
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
    shell_complete=file_completion,
    default=config_file.get_commands("list-files", "ignored_files"))
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
    default=config_file.get_commands("list-files", "all_files"))
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
    default=config_file.get_commands("list-files", "extensions"))
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
    default=config_file.get_commands("list-files", "all_extensions"))
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
    default=config_file.get_commands("list-files", "language"))
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
    default=config_file.get_commands("list-files", "all_languages"))
@option(
    "-i/-I", "--ignore-index/--keep-index", "ignore_index",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг игнорирования файлов _index любого расширения."
         "\nПо умолчанию: False, файл включается в список",
    show_default=True,
    required=False,
    default=config_file.get_commands("list-files", "ignore_index"))
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
    default=config_file.get_commands("list-files", "prefix"))
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
    default=config_file.get_commands("list-files", "no_prefix"))
@option(
    "-H", "--hidden",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг поиска скрытых файлов."
         "\nПо умолчанию: False, скрытые файлы игнорируются",
    show_default=True,
    required=False,
    default=config_file.get_commands("list-files", "hidden"))
@option(
    "-r/-R", "--recursive/--no-recursive",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг рекурсивного поиска файлов."
         "\nПо умолчанию: True, вложенные файлы учитываются",
    show_default=True,
    required=False,
    default=config_file.get_commands("list-files", "recursive"))
@option(
    "-k/-K", "--keep-logs/--remove-logs",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг сохранения директории с лог-файлом по завершении"
         "\nработы в штатном режиме."
         "\nПо умолчанию: False, лог-файл и директория удаляются",
    show_default=True,
    required=False,
    default=config_file.get_commands("list-files", "keep_logs"))
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
        extensions: set[str] = {MD_EXTENSION, ADOC_EXTENSION}

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

    if not root_dir.exists():
        echo()
        logger.warning(f"Директория {root_dir} не найдена")
        values: list[Path] | None = None

    else:
        values: list[Path] | None = walk_full(
            root_dir,
            ignored_dirs=ignored_dirs,
            ignored_files=ignored_files,
            extensions=extensions,
            language=language)

    if values is None or not values:
        if auxiliary:
            return None

        else:
            ctx.obj["keep_logs"] = keep_logs

    else:
        results: list[Path] = add_prefix(prefix, sorted(values))

        if auxiliary:
            return results

        else:
            echo(pretty_print(results))
            ctx.obj["keep_logs"] = keep_logs


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

        if listed_files:
            files.extend(map(directory.joinpath, listed_files))
            logger.debug(f"Обрабатываемые файлы:\n{pretty_print(files)}")

        else:
            logger.debug("Нет дополнительных файлов для обработки")

    return files
