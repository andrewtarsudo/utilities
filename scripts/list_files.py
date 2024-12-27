# -*- coding: utf-8 -*-
from argparse import ArgumentError, ArgumentParser, BooleanOptionalAction, Namespace, OPTIONAL, RawTextHelpFormatter, \
    SUPPRESS
from glob import iglob
from pathlib import Path

NAME: str = Path(__file__).name
STOP: str = "\nНажмите любую клавишу для завершения скрипта ...\n"


def parse():
    arg_parser: ArgumentParser = ArgumentParser(
        prog="list_files",
        usage=f"py {NAME} <ROOT_DIR>"
              f" [ -d/--ignored-dirs <DIRNAME> | --all-dirs ]"
              f" [ -e/--extensions '<EXTENSION> <EXTENSION>' | --all-ext ]"
              f" [ -f/--ignored-files <FILE> | --all-files ]"
              f" [ -l/--language <LANGUAGE> | --all-langs ]"
              f" [ -p/--prefix <PREFIX> ]"
              f" [ --hidden/--no-hidden ]"
              f" [ --recursive/--no-recursive ]"
              f" [ -v/--version ] [ -h/--help ]",
        description="Вывод файлов в директории",
        epilog="",
        add_help=False,
        allow_abbrev=False,
        exit_on_error=False,
        formatter_class=RawTextHelpFormatter
    )

    arg_parser.add_argument(
        action="store",
        nargs=OPTIONAL,
        type=str,
        default=None,
        help="Путь до директории.\nПо умолчанию: текущая директория.",
        dest="root_dir"
    )

    _dirs = arg_parser.add_mutually_exclusive_group()

    _dirs.add_argument(
        "-d", "--ignore-dirs",
        action="extend",
        default=SUPPRESS,
        required=False,
        help="Перечень игнорируемых директорий.\nМожет использоваться несколько раз.\n"
             "По умолчанию: _temp_folder, _temp_storage, private.",
        dest="ignored_dirs"
    )

    _dirs.add_argument(
        "--all-dirs",
        action="store_true",
        default=SUPPRESS,
        help="Флаг обработки всех директорий.\nПо умолчанию: False.",
        dest="all_dirs"
    )

    _suffixes = arg_parser.add_mutually_exclusive_group()

    _suffixes.add_argument(
        "-e", "--extensions",
        action="store",
        default=SUPPRESS,
        required=False,
        help="Обрабатываемые типы файлов.\nЗадаются перечислением, разделяемые пробелом.\n"
             "По умолчанию: md adoc.",
        dest="extensions"
    )

    _suffixes.add_argument(
        "--all-ext",
        action="store_true",
        default=SUPPRESS,
        help="Флаг обработки всех файлов.\nПо умолчанию: True.",
        dest="all_extensions"
    )

    _files = arg_parser.add_mutually_exclusive_group()

    _files.add_argument(
        "-f", "--ignore-files",
        action="extend",
        default=SUPPRESS,
        required=False,
        help="Перечень игнорируемых файлов.\nМожет использоваться несколько раз.\n"
             "По умолчанию: README, _check_list.",
        dest="ignored_files"
    )

    _files.add_argument(
        "--all-files",
        action="store_true",
        default=SUPPRESS,
        help="Флаг обработки всех файлов.\nПо умолчанию: False.",
        dest="all_files"
    )

    _languages = arg_parser.add_mutually_exclusive_group()

    _languages.add_argument(
        "-l", "--language",
        action="store",
        nargs=OPTIONAL,
        default=SUPPRESS,
        required=False,
        help="Язык файлов.\nПо умолчанию: ''.",
        dest="language"
    )

    _languages.add_argument(
        "--all-langs",
        action="store_true",
        default=SUPPRESS,
        help="Флаг обработки файлов всех языков.\nПо умолчанию: True.",
        dest="all_languages"
    )

    arg_parser.add_argument(
        "-p", "--prefix",
        action="store",
        default=SUPPRESS,
        required=False,
        help="Префикс, добавляемый к названиям файлов.\nПо умолчанию: ''.",
        dest="prefix"
    )

    arg_parser.add_argument(
        "--hidden",
        action=BooleanOptionalAction,
        default=SUPPRESS,
        required=False,
        help="Флаг поиска скрытых файлов.\nПо умолчанию: False.",
        dest="include_hidden"
    )

    arg_parser.add_argument(
        "--recursive",
        action=BooleanOptionalAction,
        default=SUPPRESS,
        required=False,
        help="Флаг рекурсивного поиска файлов.\nПо умолчанию: True.",
        dest="recursive"
    )

    arg_parser.add_argument(
        "-v", "--version",
        action="version",
        version="1.0.0",
        help="Показать версию скрипта и завершить работу."
    )

    arg_parser.add_argument(
        "-h", "--help",
        action="help",
        default=SUPPRESS,
        help="Показать справку и завершить работу."
    )

    try:
        args: Namespace = arg_parser.parse_args()

        if hasattr(args, "help") or hasattr(args, "version"):
            input(STOP)
            return

    except ArgumentError as exc:
        print(f"\n{exc.__class__.__name__}, {exc.argument_name}\n{exc.message}")
        input(STOP)
        exit(1)

    except KeyboardInterrupt:
        input("\nРабота скрипта остановлена пользователем ...")
        exit(2)

    else:
        return args


def get_value(namespace: Namespace, attribute: str):
    return getattr(namespace, attribute, None)


def get_files(
        root_dir: str | Path = None, *,
        extensions: str = None,
        all_extensions: bool | None = None,
        ignored_files: list[str] = None,
        all_files: bool | None = None,
        ignored_dirs: list[str] = None,
        all_dirs: bool | None = None,
        recursive: bool = None,
        include_hidden: bool = None,
        language: str = None,
        all_languages: bool | None = None,
        prefix: str = None):

    if root_dir is None:
        root_dir: Path = Path.cwd()

    else:
        root_dir: Path = Path(root_dir).resolve()

    if extensions is None and all_extensions is None:
        _parsed_extensions: list[str] = [".md", ".adoc"]

    elif extensions is None:
        _parsed_extensions: list[str] = []

    elif all_extensions is None:
        _parsed_extensions: list[str] = [
            f".{extension.removeprefix('.')}"
            for extension in extensions.strip().split(" ")]

    else:
        _parsed_extensions: list[str] = []

    if ignored_files is None and all_files is None:
        _parsed_ignored_files: list[str] = ["README", "_check_list"]

    elif ignored_files is None or not ignored_files or ignored_files == [""]:
        _parsed_ignored_files: list[str] = []

    elif all_files is None and all_files is False:
        _parsed_ignored_files: list[str] = [
            ignored_file.split(".")[-1] for ignored_file in ignored_files]

    else:
        _parsed_ignored_files: list[str] = []

    if ignored_dirs is None and all_dirs is None:
        _parsed_ignored_dirs: list[str] = ["_temp_folder", "private", "_temp_storage"]

    elif ignored_dirs is None or not ignored_dirs or ignored_dirs == [""]:
        _parsed_ignored_dirs: list[str] = []

    elif all_dirs is None and all_dirs is False:
        _parsed_ignored_dirs: list[str] = ignored_dirs

    else:
        _parsed_ignored_dirs: list[str] = []

    if recursive is None:
        recursive: bool = True

    if include_hidden is None:
        include_hidden: bool = False

    if language is None or language.lower() == "ru" or all_languages is True:
        _parsed_language: str = ""

    else:
        _parsed_language: str = language.lower()

    root_dir: Path = Path(root_dir)

    if prefix is None:
        grandparent, parent = root_dir.parts[-2], root_dir.parts[-1]

        if (grandparent, parent) == ("content", "common"):
            prefix: str = "- content/common/"
        else:
            prefix: str = ""

    _results: list[str] = []

    for item in iglob(
            "**/*", root_dir=Path(root_dir).resolve(), recursive=recursive, include_hidden=include_hidden):
        _: Path = Path(root_dir).joinpath(item)

        if _.is_dir():
            continue

        elif any(part in _parsed_ignored_dirs for part in _.parts) or _.name in _parsed_ignored_dirs:
            continue

        elif _.stem in _parsed_ignored_files:
            continue

        elif _parsed_extensions != [] and _.suffix not in _parsed_extensions:
            continue

        elif _parsed_language and not _.stem.endswith(_parsed_language):
            continue

        elif not _parsed_language and len(_.suffixes) > 1:
            continue

        else:
            _results.append(f"{prefix}{Path(item).as_posix()}")

    _results.sort()
    return _results


if __name__ == '__main__':
    ns: Namespace = parse()
    _root_dir: str = get_value(ns, "root_dir")
    _extensions: str = get_value(ns, "extensions")
    _all_extensions: bool = get_value(ns, "all_extensions")
    _ignored_files: list[str] = get_value(ns, "ignored_files")
    _all_files: bool = get_value(ns, "all_files")
    _ignored_dirs: list[str] = get_value(ns, "ignored_dirs")
    _all_dirs: bool = get_value(ns, "all_dirs")
    _recursive: bool = get_value(ns, "recursive")
    _include_hidden: bool = get_value(ns, "include_hidden")
    _language: str = get_value(ns, "language")
    _all_languages: bool = get_value(ns, "all_languages")
    _prefix: str = get_value(ns, "prefix")

    _files_str: str = "\n".join(
        get_files(
            _root_dir,
            extensions=_extensions,
            all_extensions=_all_extensions,
            ignored_files=_ignored_files,
            all_files=_all_files,
            ignored_dirs=_ignored_dirs,
            all_dirs=_all_dirs,
            recursive=_recursive,
            include_hidden=_include_hidden,
            language=_language,
            all_languages=_all_languages,
            prefix=_prefix))

    if _root_dir is None:
        _root_dir: Path = Path.cwd()

    print(f"\nФайлы в директории {Path(_root_dir).resolve()}:\n{_files_str}")
    input(STOP)
    exit()
