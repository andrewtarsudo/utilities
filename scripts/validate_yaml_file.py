# -*- coding: utf-8 -*-
from argparse import ArgumentError, ArgumentParser, Namespace, OPTIONAL, SUPPRESS
from io import UnsupportedOperation
from os import system
from pathlib import Path
from sys import platform
from typing import Any, Iterable, Mapping, get_args, get_origin

from yaml import safe_load

_SETTINGS_NAMES: tuple[str, ...] = (
    "settings", "Settings"
)
_RIGHTS_NAMES: tuple[str, ...] = (
    "rights", "Rights"
)

STOP: str = "Нажмите любую клавишу для завершения скрипта ...\n"
NAME: str = Path(__file__).name

_FAIL_: str = '\033[41m'
_PASS_: str = '\033[42m'
_NORMAL_: str = '\033[0m'

_DICT_RESULTS: dict[bool, dict[str, str]] = {
    True: {
        "status": "OK",
        "color": _PASS_
    },
    False: {
        "status": "NOT OK",
        "color": _FAIL_
    }
}


def determine_key(item: Mapping, keys: Iterable[str]):
    for key in keys:
        if key in item:
            return key

    else:
        return None


def read_yaml(path: str | Path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content: dict[str, Any] = safe_load(f)

        return content

    except FileNotFoundError:
        input(f"Файл {path} не найден. Ошибка 6")
        exit(6)

    except PermissionError:
        input(f"Недостаточно прав для записи в файл {path}. Ошибка 7")
        exit(7)

    except RuntimeError:
        input(f"Истекло время записи в файл {path}. Ошибка 8")
        exit(8)

    except UnsupportedOperation:
        input(f"Не поддерживаемая операция с файлом {path}. Ошибка 9")
        exit(9)

    except OSError as e:
        input(f"Ошибка {e.__class__.__name__}: {e.strerror}\nОшибка -1")
        exit(-1)


def inspect_settings(content: Mapping[str, Any], verbose: bool):
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
            print("Раздел settings задана корректно")


def inspect_legal(content: Mapping[str, Any], verbose: bool):
    if all(key not in content for key in iter(_RIGHTS_NAMES)):
        warnings.append("Отсутствует раздел с юридической информацией 'Rights'")

    else:
        __is_ok: bool = True

        _: str = determine_key(content, _RIGHTS_NAMES)
        rights: dict[str, dict[str, str | bool] | list[str]] = content.get(_)

        if not isinstance(rights, Mapping):
            messages.append(f"Раздел 'Rights' должен быть типа object, но получено {type(rights)}")
            __is_ok: bool = False

        if "title" not in rights:
            messages.append("В разделе 'Rights' отсутствует секция 'title'")
            __is_ok: bool = False

        else:
            title: dict[str, str | bool] = rights.get("title")

            if "title-files" not in title:
                messages.append("В секции 'Rights::title' отсутствует ключ 'title-files'")
                __is_ok: bool = False

            else:
                title_files = title.get("title-files")

                if not isinstance(title_files, bool) or title_files is not False:
                    messages.append(
                        f"Значение ключа 'Rights::title::title-files' должно быть false, "
                        f"но получено {title_files}")
                    __is_ok: bool = False

            if "value" not in title:
                messages.append("В секции 'Rights::title' отсутствует ключ 'value'")
                __is_ok: bool = False

            else:
                value = title.get("value")

                if not isinstance(value, str) or value not in ("Юридическая информация", "Legal Information"):
                    messages.append(
                        "Значение ключа 'Rights::title::value' должно быть "
                        "'Юридическая информация' или 'Legal Information', "
                        f"но получено {value}")
                    __is_ok: bool = False

        if "index" not in rights:
            messages.append("В разделе 'Rights' отсутствует секция 'index'")
            __is_ok: bool = False

        else:
            index = rights.get("index")

            if not isinstance(index, list):
                messages.append(
                    f"Значение ключа 'Rights::index' должно быть типа list, "
                    f"но получено {get_origin(index)}")
                __is_ok: bool = False

            elif not isinstance(index[0], str):
                messages.append(
                    f"Все значения ключа 'Rights::index' должны быть типа str, "
                    f"но получено {get_args(index)}")
                __is_ok: bool = False

            elif len(index) != 1:
                messages.append(
                    f"Количество значений 'Rights::index' должно быть 1, "
                    f"но получено {len(index)}")
                __is_ok: bool = False

            elif not index[0].startswith("content/common/_index"):
                messages.append(
                    f"Значение ключа 'Rights::index' должно быть 'content/common/_index.md' "
                    f"или 'content/common/_index.adoc', "
                    f"но получено {index[0]}")
                __is_ok: bool = False

        if __is_ok and verbose:
            print("Раздел Rights задан корректно")


def inspect_sections(content: Mapping[str, Any], verbose: bool):
    for name, section in content.items():
        if name in (*_SETTINGS_NAMES, *_RIGHTS_NAMES):
            continue

        else:
            if not isinstance(section, Mapping):
                messages.append(f"Раздел '{name}' должна быть типа object, но получено {type(section)}")

            else:
                __is_ok: bool = True

                if "title" in section.keys():
                    title: dict[str, str | bool] = section.get("title")

                    if "title-files" in title:
                        title_files = title.get("title-files")

                        if not isinstance(title_files, bool):
                            messages.append(
                                f"Значение ключа '{name}::title::title-files' должно быть типа bool, "
                                f"но получено {type(title_files)}")
                            __is_ok: bool = False

                    if "value" in title.keys():
                        value = title.get("value")

                        if not isinstance(value, str):
                            messages.append(
                                f"Значение ключа '{name}::title::value' должно быть типа str, "
                                f"но получено {type(value)}")
                            __is_ok: bool = False

                if "index" in section.keys():
                    index = section.get("index")

                    if not isinstance(index, list):
                        messages.append(
                            f"Значение ключа '{name}::index' должно быть типа list, "
                            f"но получено {get_origin(index)}")
                        __is_ok: bool = False

                    elif not all(isinstance(item, str) for item in index):
                        messages.append(
                            f"Все значения ключа '{name}::index' должны быть типа str, "
                            f"но получено {get_args(index)}")
                        __is_ok: bool = False

                    elif len(index) != 1:
                        messages.append(
                            f"Количество значений '{name}::index' должно быть 1, "
                            f"но получено {len(index)}")
                        __is_ok: bool = False

                if "files" in section:
                    files = section.get("files")

                    if not isinstance(files, list):
                        messages.append(
                            f"Значение ключа '{name}::files' должно быть типа list, "
                            f"но получено {get_origin(files)}")
                        __is_ok: bool = False

                    elif not all(isinstance(file, str) for file in files):
                        messages.append(
                            f"Все значения ключа '{name}::files' должны быть типа str, "
                            f"но получено {get_args(files)}")
                        __is_ok: bool = False

                if __is_ok and verbose:
                    print(f"Секция {name} задана корректно")


def read_lines(path: str | Path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            _: list[str] = f.readlines()

        return _

    except FileNotFoundError:
        input(f"Файл {path} не найден")
        raise

    except PermissionError:
        input(f"Недостаточно прав для записи в файл {path}")
        raise

    except RuntimeError:
        input(f"Истекло время записи в файл {path}")
        raise

    except UnsupportedOperation:
        input(f"Не поддерживаемая операция с файлом {path}")
        raise

    except OSError as e:
        input(f"Ошибка {e.__class__.__name__}: {e.strerror}")
        raise


def validate(root: str | Path, lines: Iterable[str], out: str | None = None, verbose: bool = False):
    paths: dict[Path, int] = {
        Path(root).joinpath(line.strip().removeprefix("- ")): index
        for index, line in enumerate(lines)
        if line.strip().startswith("- ")
    }

    max_length: int = max(map(len, map(str, paths.keys()))) + 10
    _lines: list[str] = []

    for path, line_no in paths.items():
        _result: bool = path.exists()

        _status: str = _DICT_RESULTS.get(_result).get("status")
        _color: str = _DICT_RESULTS.get(_result).get("color")

        _path: str = path.relative_to(root).as_posix()

        _line = f"{_color}{line_no + 1:>3}  {_path:.<{max_length}}{_status:.>6}{_NORMAL_}"
        _lines.append(_line)

        if verbose:
            print(_line)

        elif _status == "NOT OK":
            print(_line)

    if out is not None and out:
        out: Path = Path(out)
        mode: str = "w" if out.exists() else "x"

        with open(out, mode) as f:
            f.write(
                "\n".join(_lines).
                replace(_PASS_, "").
                replace(_FAIL_, "").
                replace(_NORMAL_, ""))

    return


def parse():
    arg_parser: ArgumentParser = ArgumentParser(
        prog="validate_yaml_file",
        usage=f"py {NAME} [ -h/--help | -v/--version ] <YAML_FILE> [ -o/--output <OUTPUT> ] [ --verbose ]",
        description="Валидация YAML-файла для PDF",
        epilog="",
        add_help=False,
        allow_abbrev=False,
        exit_on_error=False
    )

    arg_parser.add_argument(
        action="store",
        nargs=OPTIONAL,
        type=str,
        default=None,
        help="Путь до файла PDF_*.yml",
        dest="yaml_file"
    )

    arg_parser.add_argument(
        "-o", "--output",
        action="store",
        default=SUPPRESS,
        required=False,
        help="Файл для записи вывода",
        dest="output"
    )

    arg_parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Флаг подробного вывода",
        dest="verbose"
    )

    arg_parser.add_argument(
        "-v", "--version",
        action="version",
        version="1.0.0",
        help="Показать версию скрипта и завершить работу"
    )

    arg_parser.add_argument(
        "-h", "--help",
        action="help",
        default=SUPPRESS,
        help="Показать справку и завершить работу"
    )

    try:
        args: Namespace = arg_parser.parse_args()

        if hasattr(args, "help") or hasattr(args, "version"):
            input(STOP)
            exit(0)

    except ArgumentError as exc:
        print(f"{exc.__class__.__name__}, {exc.argument_name}\n{exc.message}")
        print("Ошибка 1")
        input(STOP)
        exit(1)

    except KeyboardInterrupt:
        print("Ошибка 2")
        input("Работа скрипта остановлена пользователем ...")
        exit(2)

    else:
        return args


def main():
    ns: Namespace = parse()

    if platform.startswith("win"):
        system("color")

    yaml_file: str = getattr(ns, "yaml_file")
    output: str | None = getattr(ns, "output", None)
    verbose: bool = getattr(ns, "verbose", False)

    content: dict[str, Any] = read_yaml(yaml_file)

    inspect_settings(content, verbose)
    inspect_legal(content, verbose)
    inspect_sections(content, verbose)

    if warnings or messages:
        print("Предупреждения:")
        print("\n".join(warnings))
        print("\n".join(messages))

    elif not verbose:
        print("В файле проблемы не обнаружены")

    lines: list[str] = read_lines(yaml_file)

    validate(Path(yaml_file).resolve().parent, lines, output, verbose)


if __name__ == '__main__':
    warnings: list[str] = []
    messages: list[str] = []

    main()
