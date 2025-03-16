# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, TypeAlias

FAIL_COLOR: str
PASS_COLOR: str
NORMAL_COLOR: str
separator: str
StrPath: TypeAlias = str | Path
DEBUG: Path
NORMAL: Path
PRESS_ENTER_KEY: str
HELP: str
MD_EXTENSION: str
ADOC_EXTENSION: str
MAX_SYMBOLS: int
MIN_COLUMN: int
__version__: str


class ArgsHelpDict(dict):
    SOURCES: Path

    def __init__(self) -> None: ...

    def get_multiple_keys(self, dictionary: Mapping[str, Any] = None, keys: Sequence[str] = None): ...


args_help_dict: ArgsHelpDict


def prettify(value: Any): ...


def pretty_print(values: Iterable[StrPath] = None): ...
