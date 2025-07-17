# -*- coding: utf-8 -*-
from pathlib import Path
import sys
from typing import Any, Literal, NamedTuple, Type, TypeAlias

from ruamel.yaml.compat import StringIO
from ruamel.yaml.main import YAML

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


class MyYAML(YAML):
    def dump(self, data: Any, stream: Any = None, **kwargs):
        inefficient: bool = False

        if stream is None:
            inefficient: bool = True
            stream = StringIO()

        self.indent(mapping=2, sequence=2, offset=2)
        self.width = 200
        self.encoding = "utf-8"
        self.preserve_quotes = True
        self.default_flow_style = False
        self.line_break = "\n"

        YAML.dump(self, data, stream)

        if inefficient:
            return stream.getvalue()


class ScriptVersion(NamedTuple):
    epoch: int
    major: int
    minor: int

    @classmethod
    def from_string(cls, value: str):
        """Create ScriptVersion from version string.
        Raises ValueError if string format is invalid."""
        try:
            parts: list[str] = value.split(".", 2)

            if len(parts) != 3:
                raise ValueError("Version string must contain exactly 3 parts")

            return cls(*map(int, parts))

        except ValueError as e:
            raise ValueError(f"Invalid version string '{value}': {e}") from None

    def __str__(self) -> str:
        return f"{self.epoch}.{self.major}.{self.minor}"

    def __repr__(self):
        return f"{self.__class__.__name__}<{self._asdict()}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented

        else:
            return tuple(self) == tuple(other)

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented

        else:
            return tuple(self) != tuple(other)

    def __lt__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented

        else:
            return tuple(self) < tuple(other)

    def __gt__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented

        else:
            return tuple(self) > tuple(other)

    def __le__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented

        else:
            return tuple(self) <= tuple(other)

    def __ge__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented

        else:
            return tuple(self) >= tuple(other)
