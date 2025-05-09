# -*- coding: utf-8 -*-
from pathlib import Path
import sys
from typing import Literal, Type, TypeAlias

PRESS_ENTER_KEY: str = "\nНажмите ENTER, чтобы завершить работу скрипта ..."
HELP: str = """Вывести справочную информацию на экран и завершить работу"""

SUFFIX: str = ".exe" if sys.platform.startswith("win") else ""

if getattr(sys, "frozen", False):
    BASE_PATH: Path = Path(getattr(sys, "_MEIPASS"))
    EXE_FILE: Path = Path(sys.executable)

else:
    BASE_PATH: Path = Path(__file__).parent.parent.parent
    EXE_FILE: Path = BASE_PATH.joinpath(f"bin/tw_utilities{SUFFIX}")

StrPath: TypeAlias = str | Path
ConfigType: TypeAlias = dict[str, None | str | int | dict[str, str | int | float | bool | list[str]]]
MD_EXTENSION: str = ".md"
ADOC_EXTENSION: str = ".adoc"
EXTENSIONS: tuple[str, ...] = (MD_EXTENSION, ADOC_EXTENSION)

separator: str = "=" * 100

DEBUG: Path = Path.cwd().joinpath("_logs/cli_debug.log")
NORMAL: Path = Path("~/Desktop/_logs/cli_debug.log").expanduser().resolve()

ReaderMode: Type[str] = Literal["string", "lines"]
FileType: Type[str] = Literal["json", "yaml", "toml"]

INDEX_STEMS: tuple[str, ...] = ("index", "_index")

TEMP_DIR: Path = Path.home().joinpath("_temp/")
TEMP_COMMAND_FILE: Path = TEMP_DIR.joinpath("input_command")
