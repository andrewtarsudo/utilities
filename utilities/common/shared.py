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
ConfigType: TypeAlias = dict[str, None | str | int | dict[str, str | int | float | bool | list[str]]] | None
MD_EXTENSION: str = ".md"
ADOC_EXTENSION: str = ".adoc"
EXTENSIONS: tuple[str, ...] = (MD_EXTENSION, ADOC_EXTENSION)

separator: str = "=" * 100

ReaderMode: Type[str] = Literal["string", "lines"]
FileType: Type[str] = Literal["json", "yaml", "toml"]

INDEX_STEMS: tuple[str, ...] = ("index", "_index")
