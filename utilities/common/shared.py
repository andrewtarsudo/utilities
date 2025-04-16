# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Literal, Type, TypeAlias

PRESS_ENTER_KEY: str = "\nНажмите ENTER, чтобы завершить работу скрипта ..."
HELP: str = """Вывести справочную информацию на экран и завершить работу"""
BASE_PATH: Path = Path(__file__).parent.parent.parent
StrPath: TypeAlias = str | Path
MD_EXTENSION: str = ".md"
ADOC_EXTENSION: str = ".adoc"

FAIL_COLOR: str = '\033[41m'
PASS_COLOR: str = '\033[42m'
NORMAL_COLOR: str = '\033[0m'

separator: str = "=" * 100

DEBUG: Path = Path.cwd().joinpath("_logs/cli_debug.log")
NORMAL: Path = Path("~/Desktop/_logs/cli_debug.log").expanduser().resolve()

MAX_SYMBOLS: int = 98
MIN_COLUMN: int = 5
COEFFICIENT: float = 1.0

ReaderMode: Type[str] = Literal["string", "lines"]
FileType: Type[str] = Literal["json", "yaml", "toml"]
TextType: Type[str] = Literal["md", "adoc"]

INDEX_STEMS: tuple[str, ...] = ("index", "_index")
