# -*- coding: utf-8 -*-
from pathlib import Path
from sys import platform
from typing import Any, Mapping, NamedTuple, Sequence, TypeAlias

from yaml import safe_load

FAIL_COLOR: str = '\033[41m'
PASS_COLOR: str = '\033[42m'
NORMAL_COLOR: str = '\033[0m'

separator: str = "-" * 80

StrPath: TypeAlias = str | Path

DEBUG: Path = Path.cwd().joinpath("_logs/utilities_debug.log")
NORMAL: Path = Path("~/Desktop/_logs/utilities_debug.log").expanduser().resolve()

PRESS_ENTER_KEY: str = "\nНажмите ENTER, чтобы завершить работу скрипта ..."

HELP: str = """Вывести справочную информацию на экран и завершить работу"""


class SystemInfo(NamedTuple):
    prog: str
    folder: Path

    @classmethod
    def generate(cls):
        if platform.startswith("win"):
            prog: str = f"{Path(__file__).parent.name}.exe"
            folder: Path = Path.home().joinpath("AppData/Local/TechWritersUtilities")

        elif platform.startswith("darwin"):
            prog: str = f"{Path(__file__).parent.name}"
            folder: Path = Path.home().joinpath("Library/Application Support/TechWritersUtilities")

        else:
            prog: str = f"{Path(__file__).parent.name}"
            folder: Path = Path.home().joinpath(".config/TechWritersUtilities")

        return cls(prog, folder)


class ArgsHelpDict(dict):
    SOURCES: Path = Path(__file__).parent.joinpath("../../sources/dict.yaml")

    def __init__(self):
        with open(self.__class__.SOURCES, "r", encoding="utf-8", errors="ignore") as f:
            _content: dict[str, dict[str, dict[str, str]]] = safe_load(f)

        super().__init__(**_content)

    def get_multiple_keys(self, dictionary: Mapping[str, Any] = None, keys: Sequence[str] = None):
        if dictionary is None:
            dictionary: Mapping[str, Any] = self

        if not keys:
            return dictionary

        else:
            return self.get_multiple_keys(dictionary.get(keys[0]), keys[1:])


args_help_dict: ArgsHelpDict = ArgsHelpDict()
