# -*- coding: utf-8 -*-
from argparse import ArgumentError, ArgumentParser, Namespace, ONE_OR_MORE, SUPPRESS
from pathlib import Path
from re import DOTALL, MULTILINE, Pattern, compile, sub
from typing import Iterable

from click.decorators import help_option

from cli import APIGroup, command_line_interface
from constants import HELP

NAME: str = Path(__file__).name
PRESS_ENTER_KEY: str = "\nНажмите ENTER, чтобы завершить работу скрипта ..."


def repair_svg(paths: Iterable[str | Path]):
    FOREIGN_OBJECT: Pattern = compile("<foreignObject.*?</foreignObject>", DOTALL | MULTILINE)
    TEXT: Pattern = compile(
        "<a\s?transform=\"translate(0,-5)\"\s?xlink:href=\"https://www.drawio.com/doc/faq/svg-export-text-problems"
        "\".*?</a>", DOTALL | MULTILINE)
    FEATURES: Pattern = compile(
        "<g>\s?<g\s?requiredFeatures=\"http://www.w3.org/TR/SVG11/feature#Extensibility\"/>\s?</g>", DOTALL | MULTILINE)

    for path in paths:
        path: Path = Path(path).expanduser().resolve()

        if not path.exists(follow_symlinks=True):
            print("Указан не существующий файл")
            print("Ошибка 2")
            continue

        elif not path.is_file():
            print("Путь указывает не на файл")
            print("Ошибка 3")
            continue

        elif path.suffix != ".svg":
            print("Указанный файл имеет расширение не SVG")
            print("Ошибка 4")
            continue

        else:
            try:
                with open(path, "rb") as fr:
                    svg: str = fr.read().decode()

                svg: str = sub(TEXT, "", svg)
                svg: str = sub(FOREIGN_OBJECT, "", svg)
                svg: str = sub(FEATURES, "", svg)
                svg: str = svg.replace("switch>", "g>")

                with open(path, "wb") as fw:
                    fw.write(svg.encode())

            except PermissionError:
                print(f"Недостаточно прав для записи в файл {path}")
                print("Ошибка 5")
                continue

            except RuntimeError:
                print(f"Истекло время чтения/записи файл {path}")
                print("Ошибка 6")
                continue

            except OSError as e:
                print(f"Ошибка {e.__class__.__name__}: {e.strerror}")
                print("Ошибка 7")
                continue


if __name__ == '__main__':
    arg_parser: ArgumentParser = ArgumentParser(
        prog="repair_svg",
        usage=f"py {NAME} [ -h/--help | -v/--version ] <PATH> <PATH>",
        description="Исправление файла SVG для корректного отображения",
        epilog="",
        add_help=False,
        allow_abbrev=False,
        exit_on_error=False
    )

    arg_parser.add_argument(
        action="extend",
        type=str,
        nargs=ONE_OR_MORE,
        default=None,
        help="Путь до SVG-файла. Может быть абсолютным или относительным",
        dest="paths"
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
            input(PRESS_ENTER_KEY)
            exit(0)

    except ArgumentError as e:
        print(f"{e.__class__.__name__}, {e.argument_name}\n{e.message}")
        print("Ошибка 1")
        input(PRESS_ENTER_KEY)
        exit(1)

    except KeyboardInterrupt:
        print("Ошибка -1")
        print("Работа скрипта остановлена пользователем ...")
        exit(-1)

    else:
        paths: list[str] = getattr(args, "paths")


@command_line_interface.group(
    name="repair-svg",
    cls=APIGroup,
    invoke_without_command=True)
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
def repair_svg_command():
    """"""


