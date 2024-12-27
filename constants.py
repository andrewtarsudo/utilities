# -*- coding: utf-8 -*-
from enum import Enum
from pathlib import Path
from sys import platform
from typing import Any, Mapping, Sequence

from yaml import safe_load

if platform.startswith("win"):
    _PROG: str = f"{Path(__file__).parent.name}.exe"
    _FOLDER: Path = Path.home().joinpath("AppData").joinpath("Local").joinpath("TranslationAPI")

elif platform.startswith("darwin"):
    _PROG: str = f"{Path(__file__).parent.name}"
    _FOLDER: Path = Path.home().joinpath("Library").joinpath("Application Support").joinpath("TranslationAPI")

else:
    _PROG: str = f"{Path(__file__).parent.name}"
    _FOLDER: Path = Path.home().joinpath(".config").joinpath("TranslationAPI")

_SOURCES: Path = Path(__file__).parent.parent.joinpath("sources")

PRESS_ENTER_KEY: str = "\nНажмите ENTER, чтобы завершить работу скрипта ..."

_DEBUG: Path = Path.cwd().joinpath("_logs/translation_api_debug.log")
_NORMAL: Path = Path("~/Desktop/_logs/translation_api_debug.log").expanduser().resolve()

HELP: str = """Вывести справочную информацию на экран и завершить работу"""


class Scheme(Enum):
    HTTP = "http"
    HTTPS = "https"
    FTP = "ftp"

    def __repr__(self):
        return f"<{self.__class__.__name__}['{self._name_}']>"

    def __str__(self):
        return f"{self._value_}"


class ArgsHelpDict(dict):
    def __init__(self):
        with open(_SOURCES.joinpath("dict.yaml"), "r", encoding="utf-8", errors="ignore") as f:
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
