# -*- coding: utf-8 -*-
from pathlib import Path
import sys
from typing import Literal, Type, TypeAlias

PRESS_ENTER_KEY: str = "\nНажмите ENTER, чтобы завершить работу скрипта ..."
HELP: str = """Вывести справочную информацию на экран и завершить работу"""

if getattr(sys, "frozen", False):
    BASE_PATH: Path = Path(getattr(sys, "_MEIPASS"))

else:
    BASE_PATH: Path = Path(__file__).parent.parent.parent

StrPath: TypeAlias = str | Path
MD_EXTENSION: str = ".md"
ADOC_EXTENSION: str = ".adoc"
EXTENSIONS: tuple[str, ...] = (MD_EXTENSION, ADOC_EXTENSION)

separator: str = "=" * 100

DEBUG: Path = Path.cwd().joinpath("_logs/cli_debug.log")
NORMAL: Path = Path("~/Desktop/_logs/cli_debug.log").expanduser().resolve()

MAX_SYMBOLS: int = 72
MIN_COLUMN: int = 5
COEFFICIENT: float = 1.0

ReaderMode: Type[str] = Literal["string", "lines"]
FileType: Type[str] = Literal["json", "yaml", "toml"]

INDEX_STEMS: tuple[str, ...] = ("index", "_index")
