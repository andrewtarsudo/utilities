# -*- coding: utf-8 -*-
from collections import Counter
from os import system
from pathlib import Path
from typing import Any, get_args, get_origin, Iterable, Mapping, NamedTuple

from click.core import Context
from click.decorators import argument, help_option, option, pass_context
from click.termui import style
from click.types import BOOL, Path as ClickPath
from click.utils import echo
from loguru import logger

from utilities.common.functions import file_reader, file_reader_type, file_writer, is_windows, pretty_print
from utilities.common.shared import HELP, separator, StrPath
from utilities.scripts.api_group import SwitchArgsAPIGroup
from utilities.scripts.cli import clear_logs, cli
from utilities.scripts.completion import file_dir_completion
from utilities.scripts.list_files import get_files

_SETTINGS_NAMES: tuple[str, ...] = (
    "settings", "Settings")
_RIGHTS_NAMES: tuple[str, ...] = (
    "rights", "Rights")

EPILOG: str = (
    "\b\nОпция -g/--guess пытается найти следующие файлы:"
    "\n- файлы с тем же именем, но с расширением *.md и *.adoc;"
    "\n- файлы с теми же именем и расширением, но в дочерних папках "
    "относительно той директории, "
    "\nгде должен был лежать файл."
    "\n"
    "\b\nНапример, для файла content/common/directory/file.md выполняется поиск:"
    "\n- content/common/directory/file.adoc"
    "\n- content/common/directory/first_subfolder/file.md"
    "\n- content/common/directory/first_subfolder/first_child/file.md"
    "\n- content/common/directory/first_subfolder/nth_child/file.md"
    "\n- content/common/directory/second_subfolder/file.md"
    "\n"
    "\b\nПримечание. Поиск по дочерним папкам не осуществляется для файлов index.* и _index.*, "
    "\nпоскольку в этом случае будет слишком много нерелевантных предложений.")


def determine_key(item: Mapping, keys: Iterable[str]):
    for key in keys:
        if key in item:
            return key

    return None


def detect_extra_keys(item: Mapping[str, Any]):
    extra_keys: set[str] | None = set(item.keys()).difference({"title", "index", "files"})

    if not extra_keys:
        extra_keys: set[str] | None = None

    return extra_keys


def rel(path: Path, root: Path):
    return path.relative_to(root).as_posix()


@pass_context
def fix_path(ctx: Context, line_no: int, path: Path, root: Path):
    rel_path: str = rel(path, root)

    md_file: Path = path.with_suffix(".md")
    adoc_file: Path = path.with_suffix(".adoc")

    common_part: str = f"{line_no:>4}  {style(rel_path, strikethrough=True)}"

    if md_file.exists(follow_symlinks=True):
        return f"{common_part} -> {style(rel(md_file, root), fg="red")}"

    elif adoc_file.exists(follow_symlinks=True):
        return f"{common_part} -> {style(rel(adoc_file, root), fg="red")}"

    elif path.stem.removeprefix("_") == "index":
        _: str = style(f"# {rel_path}", fg="red")
        return f"{common_part} -> {_}"

    else:
        name: str = path.name

        options: list[Path] = list(
            filter(
                lambda x: x.name == name,
                get_files(
                    ctx,
                    directory=path.parent,
                    extensions="md adoc")))

        if options:
            valid_paths: str = style(pretty_print(map(lambda x: x.relative_to(root), options)), fg="red")
            return f"{common_part} -> Возможные варианты:\n{valid_paths}"

        else:
            comment: str = style(f"# {rel_path}", fg="red")
            return f"{common_part} -> {comment}"


class GeneralInfo(NamedTuple):
    messages: list[str] = []
    warnings: list[str] = []
    options: list[str] = []
    names: set[str] = set()
    non_unique_names: set[str] = set()

    def clear(self):
        self.messages.clear()
        self.warnings.clear()
        self.options.clear()
        self.names.clear()
        self.non_unique_names.clear()


general_info: GeneralInfo = GeneralInfo()


def inspect_settings(content: Mapping[str, Any], verbose: bool):
    if all(key not in content for key in iter(_SETTINGS_NAMES)):
        general_info.messages.append("Отсутствует раздел с параметрами 'Settings'")

    else:
        __is_ok: bool = True

        _: str = determine_key(content, _SETTINGS_NAMES)
        settings: dict[str, str | int | bool] = content.get(_)

        for key in ("title-page", "version"):
            if key not in settings:
                general_info.messages.append(
                    f"В разделе 'settings' отсутствует обязательный ключ '{key}'")
                __is_ok: bool = False

            else:
                value = settings.get(key)

                if not (isinstance(value, str) or hasattr(value, "__str__")):
                    general_info.messages.append(
                        f"Значение {value} ключа {key} должно быть типа string, "
                        f"но получен {type(value)}")
                    __is_ok: bool = False

        if __is_ok and verbose:
            general_info.messages.append("Раздел 'settings' задан корректно")


def inspect_legal(content: Mapping[str, Any], verbose: bool):
    if all(key not in content for key in iter(_RIGHTS_NAMES)):
        general_info.warnings.append("Отсутствует раздел с юридической информацией 'Rights'")

    else:
        __is_ok: bool = True

        _: str = determine_key(content, _RIGHTS_NAMES)
        rights: dict[str, dict[str, str | bool] | list[str]] = content.get(_)

        if not isinstance(rights, Mapping):
            general_info.warnings.append(f"Раздел 'Rights' должен быть типа object, но получено {type(rights)}")
            __is_ok: bool = False

        if "title" not in rights:
            general_info.warnings.append("В разделе 'Rights' отсутствует секция 'title'")
            __is_ok: bool = False

        else:
            title: dict[str, str | bool] = rights.get("title")

            if "title-files" not in title:
                general_info.warnings.append("В секции 'Rights::title' отсутствует ключ 'title-files'")
                __is_ok: bool = False

            else:
                title_files = title.get("title-files")

                if not isinstance(title_files, bool) or title_files is not False:
                    general_info.warnings.append(
                        f"Значение ключа 'Rights::title::title-files' должно быть false, "
                        f"но получено {title_files}")
                    __is_ok: bool = False

            if "value" not in title:
                general_info.warnings.append("В секции 'Rights::title' отсутствует ключ 'value'")
                __is_ok: bool = False

            else:
                value = title.get("value")

                if not isinstance(value, str) or value not in ("Юридическая информация", "Legal Information"):
                    general_info.warnings.append(
                        "Значение ключа 'Rights::title::value' должно быть "
                        "'Юридическая информация' или 'Legal Information', "
                        f"но получено {value}")
                    __is_ok: bool = False

        if "index" not in rights:
            general_info.warnings.append("В разделе 'Rights' отсутствует секция 'index'")
            __is_ok: bool = False

        else:
            index = rights.get("index")

            if not isinstance(index, list):
                general_info.warnings.append(
                    f"Значение ключа 'Rights::index' должно быть типа list, "
                    f"но получено {get_origin(index)}")
                __is_ok: bool = False

            elif not isinstance(index[0], str):
                general_info.warnings.append(
                    f"Все значения ключа 'Rights::index' должны быть типа str, "
                    f"но получено {get_args(index)}")
                __is_ok: bool = False

            elif len(index) != 1:
                general_info.warnings.append(
                    f"Количество значений 'Rights::index' должно быть 1, "
                    f"но получено {len(index)}")
                __is_ok: bool = False

            elif not index[0].startswith("content/common/_index"):
                general_info.warnings.append(
                    f"Значение ключа 'Rights::index' должно быть 'content/common/_index.md' "
                    f"или 'content/common/_index.adoc', "
                    f"но получено {index[0]}")
                __is_ok: bool = False

        if (extra_keys := detect_extra_keys({**rights})) is not None:
            general_info.warnings.append(
                f"В разделе Rights обнаружены посторонние ключи:\n{pretty_print(extra_keys)}")

        if __is_ok and verbose:
            general_info.messages.append("Раздел 'Rights' задан корректно")


def inspect_sections(content: Mapping[str, Any], verbose: bool):
    for name, section in content.items():
        if name in general_info.names:
            general_info.non_unique_names.add(name)

        else:
            general_info.names.add(name)

        if name in (*_SETTINGS_NAMES, *_RIGHTS_NAMES):
            continue

        elif name.endswith("cross_docs"):
            general_info.warnings.append(
                f"Обнаружен раздел {name}, в котором ссылки ведут в другой проект.\n"
                "На данный момент такие секции пропускаются при проверке")
            continue

        else:
            if not isinstance(section, Mapping):
                general_info.messages.append(f"Раздел '{name}' должна быть типа object, но получено {type(section)}")

            else:
                __is_ok: bool = True

                if "title" in section.keys():
                    title: dict[str, str | bool] = section.get("title", {})

                    if title is None or not title:
                        general_info.warnings.append(f"В разделе {name} объявлена секция title, хотя она пуста")
                        __is_ok: bool = False

                    else:
                        if "title-files" in title:
                            title_files = title.get("title-files")

                            if not isinstance(title_files, bool):
                                general_info.warnings.append(
                                    f"Значение ключа '{name}::title::title-files' должно быть типа bool, "
                                    f"но получено {type(title_files)}")
                                __is_ok: bool = False

                        if "value" in title.keys():
                            value = title.get("value")

                            if not isinstance(value, str):
                                general_info.warnings.append(
                                    f"Значение ключа '{name}::title::value' должно быть типа str, "
                                    f"но получено {type(value)}")
                                __is_ok: bool = False

                        if "level" in title.keys():
                            level = title.get("level")

                            if not isinstance(level, int):
                                general_info.warnings.append(
                                    f"Значение ключа '{name}::title::level' должно быть типа int, "
                                    f"но получено {type(level).__name__}")
                                __is_ok: bool = False

                            elif level < 0 or level > 9:
                                general_info.messages.append(
                                    f"Значение ключа '{name}::title::level' должно быть "
                                    f"целым неотрицательным числом в диапазоне [0-9], "
                                    f"но получено {level}")
                                __is_ok: bool = False

                        for key in title.keys():
                            if key not in ("title-files", "value", "level"):
                                general_info.warnings.append(
                                    f"Ключ {key} не ожидается в секции title раздела {name}")

                if "index" in section.keys():
                    index = section.get("index")

                    if index is None or not index:
                        general_info.warnings.append(f"В разделе {name} объявлена секция index, хотя она пуста")
                        __is_ok: bool = False

                    elif not isinstance(index, list):
                        general_info.warnings.append(
                            f"Значение ключа '{name}::index' должно быть типа list, "
                            f"но получено {get_origin(index)}")
                        __is_ok: bool = False

                    elif not all(isinstance(item, str) for item in index):
                        general_info.warnings.append(
                            f"Все значения ключа '{name}::index' должны быть типа str, "
                            f"но получено {get_args(index)}")
                        __is_ok: bool = False

                    elif len(index) != 1:
                        general_info.warnings.append(
                            f"Количество значений '{name}::index' должно быть 1, "
                            f"но получено {len(index)}")
                        __is_ok: bool = False

                if "files" in section.keys():
                    files = section.get("files")

                    if files is None or not files:
                        general_info.warnings.append(f"В разделе {name} объявлена секция files, хотя она пуста")

                    elif not isinstance(files, list):
                        general_info.warnings.append(
                            f"Значение ключа '{name}::files' должно быть типа list, "
                            f"но получено {get_origin(files)}")
                        __is_ok: bool = False

                    elif not all(isinstance(file, str) for file in files):
                        general_info.warnings.append(
                            f"Все значения ключа '{name}::files' должны быть типа str, "
                            f"но получено {get_args(files)}")
                        __is_ok: bool = False

                if (extra_keys := detect_extra_keys({**section})) is not None:
                    general_info.warnings.append(
                        f"В разделе {name} обнаружены посторонние ключи:\n{pretty_print(extra_keys)}")

                if __is_ok and verbose:
                    general_info.messages.append(f"Раздел {name} задан корректно")


def find_non_unique(lines: list[str]):
    keys: dict[int, str] = {
        index: line.strip("\n")
        for index, line in enumerate(iter(lines))
        if not line.startswith(" ") and not line.strip().startswith("#") and line.strip("\n")}

    counter: Counter = Counter(keys.values())
    repeating: list[str] = [key for key, value in counter.items() if value > 1]
    non_unique: dict[str, list[int]] = {_: [] for _ in repeating}

    for k, v in keys.items():
        if v in repeating:
            non_unique[v].append(k)

    general_info.warnings.extend(
        f"Ключ {_non_unique_key} не уникален: повторяется в строках: "
        f"{', '.join(map(str, _non_unique_value))}"
        for _non_unique_key, _non_unique_value in non_unique.items())


def validate_file(
        root: StrPath,
        lines: Iterable[str], *,
        output: str | None = None,
        guess: bool = True,
        verbose: bool = False):
    max_length: int = max(map(len, lines)) + 3

    paths: dict[int, Path] = {
        index: Path(root).joinpath(line.strip().removeprefix("- "))
        for index, line in enumerate(lines)
        if line.strip().startswith("- ") and ".." not in line}

    _lines: list[str] = []

    _DICT_RESULTS: dict[bool, dict[str, str]] = {
        True: {
            "status": "OK",
            "color": "green"},
        False: {
            "status": "FAIL",
            "color": "red"}}

    for line_no, path in paths.items():
        _result: bool = path.exists() and path.as_posix().endswith(("md", "adoc"))

        _status: str = _DICT_RESULTS[_result]["status"]
        _color: str = _DICT_RESULTS[_result]["color"]

        _path: str = path.relative_to(root).as_posix()

        _line: str = style(f"{line_no + 1:>4}  {_path: <{max_length}}{_status: >5}", bg=_color)
        _lines.append(_line)

        if verbose or _status == "FAIL":
            echo(_line)

        if _status == "FAIL" and guess is True:
            general_info.options.append(fix_path(line_no + 1, path, root))

    if output is not None and output:
        output: Path = Path(output).expanduser()
        output.unlink(missing_ok=True)
        output.touch(exist_ok=True)

        file_writer(output, _lines)


@cli.command(
    "validate-yaml",
    cls=SwitchArgsAPIGroup,
    help="Команда для валидации YAML-файла, используемого при генерации PDF",
    epilog=EPILOG)
@argument(
    "file_or_project",
    type=ClickPath(
        exists=True,
        file_okay=True,
        allow_dash=False,
        dir_okay=True),
    required=True,
    shell_complete=file_dir_completion)
@option(
    "-o", "--output",
    type=ClickPath(
        file_okay=True,
        writable=True,
        resolve_path=True,
        allow_dash=True,
        dir_okay=False),
    help="\b\nФайл для записи вывода. По умолчанию: вывод в консоль",
    multiple=False,
    required=False,
    metavar="FILE",
    default=None)
@option(
    "-g/-G", "--guess/--no-guess", "guess",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг вывода возможных корректных путей."
         "\nПо умолчанию: True, отображаются предполагаемые замены",
    show_default=True,
    required=False,
    default=True)
@option(
    "-v/-q", "--verbose/--quiet", "verbose",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг подробного вывода.\nПо умолчанию: False, выводятся только ошибки",
    show_default=True,
    required=False,
    default=False)
@option(
    "-k/-K", "--keep-logs/--remove-logs", "keep_logs",
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
def validate_yaml_command(
        ctx: Context,
        file_or_project: StrPath,
        output: StrPath = None,
        guess: bool = True,
        verbose: bool = False,
        keep_logs: bool = False):
    if is_windows():
        system("color")

    file_or_project: Path = Path(file_or_project).expanduser()

    if output == "-":
        output: StrPath | None = None

    if file_or_project.is_dir():
        yaml_files: list[Path] = [
            yaml_file for yaml_file in file_or_project.iterdir()
            if yaml_file.suffix == ".yml" and not yaml_file.stem.startswith(".")]

    elif file_or_project.is_file():
        yaml_files: list[Path] = [file_or_project]

    else:
        logger.error(f"Некорректное значение file_or_project: {file_or_project}, {type(file_or_project).__name__}")
        raise ValueError

    if not yaml_files:
        logger.warning("Не найдены подходящие файлы в указанной директории или указанный файл не является YAML")

    else:
        for yaml_file in yaml_files:
            yaml_file: Path = Path(yaml_file).expanduser().resolve()
            echo(style(separator, fg="magenta"))
            echo(f"Файл {yaml_file.name}:")

            content: dict[str, Any] = file_reader_type(yaml_file, "yaml")

            inspect_settings(content, verbose)
            inspect_legal(content, verbose)
            inspect_sections(content, verbose)

            lines: list[str] = file_reader(yaml_file, "lines")

            find_non_unique(lines)
            validate_file(yaml_file.parent, lines, output=output, guess=guess, verbose=verbose)

            if general_info.warnings:
                _warnings: str = pretty_print(general_info.warnings)
                echo("\nПредупреждения:")
                echo(_warnings)
                logger.debug(_warnings)

            if guess and general_info.options:
                _options: str = pretty_print(general_info.options)
                echo("\nИсправления:")
                echo(_options)
                logger.debug(_options)

            if verbose and general_info.messages:
                _messages: str = pretty_print(general_info.messages)
                echo("\nСообщения:")
                echo(_messages)
                logger.debug(_messages)

            if not (verbose or general_info.warnings or general_info.messages or general_info.options):
                logger.success("Проблемы с парамерами разделов не обнаружены\n")

            general_info.clear()

    if output is not None:
        echo(f"Файл с результатами: {output.resolve()}")

    ctx.obj["keep_logs"] = keep_logs
    ctx.invoke(clear_logs)
