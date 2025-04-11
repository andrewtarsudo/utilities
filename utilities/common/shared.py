# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, TypeAlias

from yaml import safe_load

FAIL_COLOR: str = '\033[41m'
PASS_COLOR: str = '\033[42m'
NORMAL_COLOR: str = '\033[0m'

separator: str = "-" * 80

StrPath: TypeAlias = str | Path

BASE_PATH: Path = Path(__file__).parent.parent.parent

DEBUG: Path = Path.cwd().joinpath("_logs/cli_debug.log")
NORMAL: Path = Path("~/Desktop/_logs/cli_debug.log").expanduser().resolve()

PRESS_ENTER_KEY: str = "\nНажмите ENTER, чтобы завершить работу скрипта ..."

HELP: str = """Вывести справочную информацию на экран и завершить работу"""

MD_EXTENSION: str = ".md"
ADOC_EXTENSION: str = ".adoc"

MAX_SYMBOLS: int = 98
MIN_COLUMN: int = 5
COEFFICIENT: float = 1.0


class ArgsHelpDict(dict):
    SOURCES: Path = BASE_PATH.joinpath("sources/dict.yaml")

    def __init__(self):
        with open(self.__class__.SOURCES, "r", encoding="utf-8", errors="ignore") as f:
            _content: dict[str, dict[str, str]] = safe_load(f)

        super().__init__()
        self.update(**_content)

    def get_multiple_keys(self, *, dictionary: Mapping[str, Any] = None, keys: Sequence[str] = None):
        if dictionary is None:
            dictionary: Mapping[str, Any] = self

        if not keys:
            return dictionary

        else:
            return self.get_multiple_keys(dictionary=dictionary.get(keys[0]), keys=keys[1:])

    @property
    def max_key(self) -> int:
        return max(len(k) for _, values in self.items() for k, _ in values.items()) + 2 + 4


args_help_dict: ArgsHelpDict = ArgsHelpDict()


def _prettify(value: Any):
    return str(value).strip()


def pretty_print(values: Iterable[StrPath] = None):
    if values is None or not values:
        return ""

    elif isinstance(values, str):
        return f"{values}"

    else:
        return "\n".join(map(_prettify, values))
