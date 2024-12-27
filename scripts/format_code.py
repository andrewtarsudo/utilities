# -*- coding: utf-8 -*-
from argparse import ArgumentError, ArgumentParser, Namespace, ONE_OR_MORE, SUPPRESS
from pathlib import Path
from re import Match, finditer
from typing import Iterable

from loguru import logger

_MAX_LENGTH: int = 84
STOP: str = "Нажмите любую клавишу для завершения скрипта ...\n"
NAME: str = Path(__file__).parent.name


def check_path_file(path: str | Path):
    path: Path = Path(path).expanduser().resolve()

    if not path.exists():
        logger.error(f"Путь {path} не существует")
        raise FileNotFoundError

    if not path.is_file():
        logger.error(f"Путь {path} указывает не на директорию")
        raise IsADirectoryError

    return


def split(line: str, start: int = 0, length: int = _MAX_LENGTH, split_lines: Iterable[str] = None) -> list[str] | None:
    if split_lines is None:
        split_lines: list[str] = []
    else:
        split_lines: list[str] = [*split_lines]

    if len(line) <= length:
        split_lines.append(line)
        return split_lines

    while start < len(line) - 1:
        end: int = min(start + length, len(line))

        _slice: str = line[start:end]

        if end < len(line):
            _matches: list[Match] = list(finditer(";", _slice))

            if not _matches:
                stop_br: int = _slice.rfind("[")
                stop_comma: int = _slice.rfind(",")

                stop: int = max(stop_br, stop_comma)

                if stop == -1:
                    stop: int = len(_slice) - 1

            else:
                _last: Match = _matches[-1]
                stop: int = _last.end()

            if stop <= 0:
                logger.error("Ошибка разбиения файла на части")
                raise OSError

        else:
            stop: int = len(line) - start

        split_line: str = line[start:start + stop]
        split_lines.append(split_line)

        start += stop

        split(line, start, length, split_lines)

    else:
        return split_lines


def fix_code_length(file: str | Path, length: int = _MAX_LENGTH):
    check_path_file(file)

    with open(file, "r", encoding="utf-8", errors="ignore") as fr:
        _content: str = fr.read()

    _result: list[str] = []

    for code in finditer("`{3}\S*\n(.*?)\n`{3}", _content):
        lines: list[str] = code.group(1).splitlines()

        for line in lines:
            _: list[str] = split(line, length=length)
            _result.append("\n".join(_))

    with open(file, "w", encoding="utf-8", errors="ignore") as fw:
        fw.write("\n\n".join(_result))


def parse():
    # specify the cli options
    arg_parser: ArgumentParser = ArgumentParser(
        prog="format_code",
        usage=f"py {NAME} [ -h/--help | -v/--version ] <FILE> .. <FILE> [ -l/--length <LENGTH> ]",
        description="Форматирование кода для удобного отображения в PDF",
        epilog="",
        add_help=False,
        allow_abbrev=False,
        exit_on_error=False
    )

    arg_parser.add_argument(
        "files",
        action="extend",
        nargs=ONE_OR_MORE,
        default=SUPPRESS,
        help="Файлы для обработки"
    )

    arg_parser.add_argument(
        "-l", "--length",
        action="store",
        type=int,
        default=_MAX_LENGTH,
        help="Максимальная длина строки",
        dest="length"
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

    # parse the user input
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


if __name__ == '__main__':
    ns: Namespace = parse()

    files: list[str] = getattr(ns, "files", list())
    length: int = getattr(ns, "length")

    for file in files:
        fix_code_length(file, length)


