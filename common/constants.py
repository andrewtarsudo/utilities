# -*- coding: utf-8 -*-
from pathlib import Path
from sys import platform
from typing import Any, Mapping, NamedTuple, Sequence

from yaml import safe_load

FAIL_COLOR: str = '\033[41m'
PASS_COLOR: str = '\033[42m'
NORMAL_COLOR: str = '\033[0m'


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


SOURCES: Path = Path(__file__).parent

PRESS_ENTER_KEY: str = "\nНажмите ENTER, чтобы завершить работу скрипта ..."

HELP: str = """Вывести справочную информацию на экран и завершить работу"""


class ArgsHelpDict(dict):
    def __init__(self):
        with open(SOURCES.joinpath("../dict.yaml"), "r", encoding="utf-8", errors="ignore") as f:
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
