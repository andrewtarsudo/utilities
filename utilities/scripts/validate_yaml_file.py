# -*- coding: utf-8 -*-
from io import UnsupportedOperation
from os import system
from pathlib import Path
from sys import platform
from typing import Any, get_args, get_origin, Iterable, Mapping

from click.core import Context
from click.decorators import argument, help_option, option, pass_context
from click.types import BOOL, Path as ClickPath
from click.utils import echo
from loguru import logger
from yaml import safe_load

from utilities.common.constants import FAIL_COLOR, HELP, NORMAL_COLOR, PASS_COLOR, pretty_print, StrPath
from utilities.common.functions import file_reader, ReaderMode
from utilities.scripts.cli import clear_logs, command_line_interface, SwitchArgsAPIGroup

_ALLOWED_KEYS: tuple[str, ...] = ("title", "index", "files")

_SETTINGS_NAMES: tuple[str, ...] = (
    "settings", "Settings"
)
_RIGHTS_NAMES: tuple[str, ...] = (
    "rights", "Rights"
)

_DICT_RESULTS: dict[bool, dict[str, str]] = {
    True: {
        "status": "OK",
        "color": PASS_COLOR
    },
    False: {
        "status": "NOT OK",
        "color": FAIL_COLOR
    }
}


def determine_key(item: Mapping, keys: Iterable[str]):
    for key in keys:
        if key in item:
            return key

    else:
        return None


def detect_extra_keys(item: Mapping[str, Any]):
    extra_keys: set[str] | None = set(item.keys()).difference(_ALLOWED_KEYS)

    if not extra_keys:
        extra_keys: set[str] | None = None

    return extra_keys


def inspect_settings(
        content: Mapping[str, Any],
        verbose: bool,
        warnings: Iterable[str] = None,
        messages: Iterable[str] = None):
    if warnings is None:
        warnings: list[str] = []

    else:
        warnings: list[str] = [*warnings]

    if messages is None:
        messages: list[str] = []

    else:
        messages: list[str] = [*messages]

    if all(key not in content for key in iter(_SETTINGS_NAMES)):
        messages.append("Отсутствует раздел с параметрами 'Settings'")

    else:
        __is_ok: bool = True

        _: str = determine_key(content, _SETTINGS_NAMES)
        settings: dict[str, str | int | bool] = content.get(_)

        for key in ("title-page", "version"):
            if key not in settings:
                messages.append(
                    f"В разделе 'settings' отсутствует обязательный ключ '{key}'")
                __is_ok: bool = False

            else:
                value = settings.get(key)

                if not (isinstance(value, str) or hasattr(value, "__str__")):
                    messages.append(
                        f"Значение {value} ключа {key} должно быть типа string, "
                        f"но получен {type(value)}")
                    __is_ok: bool = False

        if __is_ok and verbose:
            messages.append("Раздел 'settings' задан корректно")

    return warnings, messages


def inspect_legal(
        content: Mapping[str, Any],
        verbose: bool,
        warnings: Iterable[str] = None,
        messages: Iterable[str] = None):
    if warnings is None:
        warnings: list[str] = []

    else:
        warnings: list[str] = [*warnings]

    if messages is None:
        messages: list[str] = []

    else:
        messages: list[str] = [*messages]

    if all(key not in content for key in iter(_RIGHTS_NAMES)):
        warnings.append("Отсутствует раздел с юридической информацией 'Rights'")

    else:
        __is_ok: bool = True

        _: str = determine_key(content, _RIGHTS_NAMES)
        rights: dict[str, dict[str, str | bool] | list[str]] = content.get(_)

        if not isinstance(rights, Mapping):
            warnings.append(f"Раздел 'Rights' должен быть типа object, но получено {type(rights)}")
            __is_ok: bool = False

        if "title" not in rights:
            warnings.append("В разделе 'Rights' отсутствует секция 'title'")
            __is_ok: bool = False

        else:
            title: dict[str, str | bool] = rights.get("title")

            if "title-files" not in title:
                warnings.append("В секции 'Rights::title' отсутствует ключ 'title-files'")
                __is_ok: bool = False

            else:
                title_files = title.get("title-files")

                if not isinstance(title_files, bool) or title_files is not False:
                    warnings.append(
                        f"Значение ключа 'Rights::title::title-files' должно быть false, "
                        f"но получено {title_files}")
                    __is_ok: bool = False

            if "value" not in title:
                warnings.append("В секции 'Rights::title' отсутствует ключ 'value'")
                __is_ok: bool = False

            else:
                value = title.get("value")

                if not isinstance(value, str) or value not in ("Юридическая информация", "Legal Information"):
                    warnings.append(
                        "Значение ключа 'Rights::title::value' должно быть "
                        "'Юридическая информация' или 'Legal Information', "
                        f"но получено {value}")
                    __is_ok: bool = False

        if "index" not in rights:
            warnings.append("В разделе 'Rights' отсутствует секция 'index'")
            __is_ok: bool = False

        else:
            index = rights.get("index")

            if not isinstance(index, list):
                warnings.append(
                    f"Значение ключа 'Rights::index' должно быть типа list, "
                    f"но получено {get_origin(index)}")
                __is_ok: bool = False

            elif not isinstance(index[0], str):
                warnings.append(
                    f"Все значения ключа 'Rights::index' должны быть типа str, "
                    f"но получено {get_args(index)}")
                __is_ok: bool = False

            elif len(index) != 1:
                warnings.append(
                    f"Количество значений 'Rights::index' должно быть 1, "
                    f"но получено {len(index)}")
                __is_ok: bool = False

            elif not index[0].startswith("content/common/_index"):
                warnings.append(
                    f"Значение ключа 'Rights::index' должно быть 'content/common/_index.md' "
                    f"или 'content/common/_index.adoc', "
                    f"но получено {index[0]}")
                __is_ok: bool = False

        if (extra_keys := detect_extra_keys({**rights})) is not None:
            warnings.append(
                f"В разделе Rights обнаружены посторонние ключи:\n{pretty_print(extra_keys)}")

        if __is_ok and verbose:
            messages.append("Раздел 'Rights' задан корректно")

    return warnings, messages


def inspect_sections(
        content: Mapping[str, Any],
        verbose: bool,
        warnings: Iterable[str] = None,
        messages: Iterable[str] = None):
    if warnings is None:
        warnings: list[str] = []

    else:
        warnings: list[str] = [*warnings]

    if messages is None:
        messages: list[str] = []

    else:
        messages: list[str] = [*messages]

    for name, section in content.items():
        if name in (*_SETTINGS_NAMES, *_RIGHTS_NAMES):
            continue

        elif name.endswith("cross_docs"):
            warnings.append(
                f"Обнаружен раздел {name}, в котором ссылки ведут в другой проект.\n"
                "На данный момент такие секции пропускаются при проверке")
            continue

        else:
            if not isinstance(section, Mapping):
                messages.append(f"Раздел '{name}' должна быть типа object, но получено {type(section)}")

            else:
                __is_ok: bool = True

                if "title" in section.keys():
                    title: dict[str, str | bool] = section.get("title", dict())

                    if title is None:
                        warnings.append(f"В разделе {name} объявлена секция title, хотя она пуста")
                        __is_ok: bool = False

                    else:
                        if "title-files" in title:
                            title_files = title.get("title-files")

                            if not isinstance(title_files, bool):
                                warnings.append(
                                    f"Значение ключа '{name}::title::title-files' должно быть типа bool, "
                                    f"но получено {type(title_files)}")
                                __is_ok: bool = False

                        if "value" in title.keys():
                            value = title.get("value")

                            if not isinstance(value, str):
                                warnings.append(
                                    f"Значение ключа '{name}::title::value' должно быть типа str, "
                                    f"но получено {type(value)}")
                                __is_ok: bool = False

                        if "level" in title.keys():
                            level = title.get("level")

                            if not isinstance(level, int):
                                warnings.append(
                                    f"Значение ключа '{name}::title::level' должно быть типа int, "
                                    f"но получено {type(level)}")
                                __is_ok: bool = False

                            elif level < 0:
                                messages.append(
                                    f"Значение ключа '{name}::title::level' должно быть неотрицательным, "
                                    f"но получено {level}")
                                __is_ok: bool = False

                            elif level > 5:
                                messages.append(
                                    f"Значение ключа '{name}::title::level' должно быть целым числом, диапазон: [0-5], "
                                    f"но получено {level}")
                                __is_ok: bool = False

                if "index" in section.keys():
                    index = section.get("index")

                    if index is None:
                        warnings.append(f"В разделе {name} объявлена секция index, хотя она пуста")
                        __is_ok: bool = False

                    elif not isinstance(index, list):
                        warnings.append(
                            f"Значение ключа '{name}::index' должно быть типа list, "
                            f"но получено {get_origin(index)}")
                        __is_ok: bool = False

                    elif not all(isinstance(item, str) for item in index):
                        warnings.append(
                            f"Все значения ключа '{name}::index' должны быть типа str, "
                            f"но получено {get_args(index)}")
                        __is_ok: bool = False

                    elif len(index) != 1:
                        warnings.append(
                            f"Количество значений '{name}::index' должно быть 1, "
                            f"но получено {len(index)}")
                        __is_ok: bool = False

                if "files" in section.keys():
                    files = section.get("files")

                    if not isinstance(files, list):
                        warnings.append(
                            f"Значение ключа '{name}::files' должно быть типа list, "
                            f"но получено {get_origin(files)}")
                        __is_ok: bool = False

                    elif not all(isinstance(file, str) for file in files):
                        warnings.append(
                            f"Все значения ключа '{name}::files' должны быть типа str, "
                            f"но получено {get_args(files)}")
                        __is_ok: bool = False

                if (extra_keys := detect_extra_keys({**section})) is not None:
                    warnings.append(
                        f"В разделе {name} обнаружены посторонние ключи:\n{pretty_print(extra_keys)}")

                if __is_ok and verbose:
                    messages.append(f"Раздел {name} задан корректно")

    return warnings, messages


def validate(
        root: StrPath,
        lines: Iterable[str],
        out: str | None = None,
        verbose: bool = False):
    max_length: int = max(map(len, lines)) + 5

    paths: dict[int, Path] = {
        index: Path(root).joinpath(line.strip().removeprefix("- "))
        for index, line in enumerate(lines)
        if line.strip().startswith("- ") and ".." not in line
    }

    _lines: list[str] = []

    for line_no, path in paths.items():
        _result: bool = path.resolve().exists()

        _status: str = _DICT_RESULTS.get(_result).get("status")
        _color: str = _DICT_RESULTS.get(_result).get("color")

        _path: str = path.relative_to(root).as_posix()

        _line = f"{_color}{line_no + 1:>4}  {_path:.<{max_length}}{_status:.>6}{NORMAL_COLOR}"
        _lines.append(_line)

        if verbose or _status == "NOT OK":
            echo(_line)

    if out is not None and out:
        out: Path = Path(out).expanduser()
        mode: str = "w" if out.exists() else "x"

        with open(out, mode) as f:
            f.write(
                pretty_print(_lines).
                replace(PASS_COLOR, "").
                replace(FAIL_COLOR, "").
                replace(NORMAL_COLOR, ""))


@command_line_interface.command(
    "validate-yaml",
    cls=SwitchArgsAPIGroup,
    help="Команда для валидации YAML-файла, используемого при генерации PDF")
@argument(
    "yaml_file",
    type=ClickPath(
        file_okay=True,
        readable=True,
        allow_dash=False,
        dir_okay=False),
    required=True)
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
    "--verbose/--no-verbose",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг подробного вывода.\nПо умолчанию: False, выводятся только ошибки",
    show_default=True,
    required=False,
    default=False)
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
def validate_yaml_command(
        ctx: Context,
        yaml_file: StrPath,
        output: StrPath = None,
        verbose: bool = False,
        keep_logs: bool = False):
    if platform.startswith("win"):
        system("color")

    yaml_file: Path = Path(yaml_file).expanduser().resolve()

    try:
        with open(yaml_file, "r", encoding="utf-8", errors="ignore") as f:
            content: dict[str, Any] = safe_load(f)

    except FileNotFoundError:
        logger.error(f"Файл {yaml_file} не найден")

    except PermissionError:
        logger.error(f"Недостаточно прав для чтения файла {yaml_file}")

    except RuntimeError:
        logger.error(f"Истекло время чтения файла {yaml_file}")

    except UnsupportedOperation:
        logger.error(f"Не поддерживаемая операция с файлом {yaml_file}")

    except UnboundLocalError as e:
        logger.error(f"Ошибка присваивания {e.name}")

    except OSError as e:
        logger.error(f"Ошибка {e.__class__.__name__}: {e.strerror}")

    else:
        warnings: list[str] = []
        messages: list[str] = []

        warnings, messages = inspect_settings(content, verbose, warnings, messages)
        warnings, messages = inspect_legal(content, verbose, warnings, messages)
        warnings, messages = inspect_sections(content, verbose, warnings, messages)

        if warnings:
            logger.warning("Предупреждения:")
            logger.warning(pretty_print(warnings))

        elif messages:
            logger.warning(pretty_print(messages))

        elif not verbose:
            echo("Проблемы с парамерами разделов не обнаружены\n")

        lines: list[str] = file_reader(yaml_file, ReaderMode.LINES)
        validate(yaml_file.parent, lines, output, verbose)

        if output is not None:
            echo(f"Файл с результатами: {output.resolve()}")

    finally:
        ctx.obj["keep_logs"] = keep_logs
        ctx.invoke(clear_logs)
