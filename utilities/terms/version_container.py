# -*- coding: utf-8 -*-
from collections import Counter
from pathlib import Path
from typing import NamedTuple

from loguru import logger

from utilities.common.shared import StrPath
from utilities.common.errors import TermsInvalidTypeVersionError, TermsInvalidVersionError
from utilities.common.functions import file_reader


class Version(NamedTuple):
    day: int | str
    month: int | str
    year: int | str

    def __str__(self):
        return f"{self.day}.{self.month}.{self.year}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>({self.day}.{self.month}.{self.year})"

    def __key(self) -> tuple[str, ...]:
        return f"{self.day}", f"{self.month}", f"{self.year}"

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        elif self.__key() == ("0", "0", "0"):
            return False

        else:
            return self.__key() == other.__key()

    def __ne__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        elif self.__key() == ("0", "0", "0"):
            return True

        else:
            return self.__key() != other.__key()

    def __bool__(self):
        return str(self) == "0.0.0"

    @classmethod
    def from_string(cls, line: str):
        if not line:
            return cls(0, 0, 0)

        elif Counter(line).get(".") != 2:
            logger.error(f"Версия должна иметь вид: day.month.year, но получено {line}")
            raise TermsInvalidVersionError

        else:
            day, month, year = line.split(".")
            return cls(day, month, year)


class VersionContainer:
    def __init__(self, version_file: StrPath, basic_version_file: StrPath):
        self._version_file: Path = Path(version_file)
        self._basic_version_file: Path = Path(basic_version_file)

        self._version: Version | None = None
        self._version_basic: Version | None = None

    def __str__(self):
        return f"<{self.__class__.__name__}>"

    def __repr__(self):
        return f"<{self.__class__.__name__}> version={self._version}, version_basic={self._version_basic}"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return True

        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return False

        else:
            return NotImplemented

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        if isinstance(value, Version):
            self._version = value

        elif isinstance(value, str):
            try:
                version: Version = Version.from_string(value)

            except TermsInvalidVersionError:
                logger.error("Некорректная структура файла версии")
                raise

            else:
                self._version = version

        else:
            logger.error(f"Значение {value} должно быть типа Version или str, но получено {type(value).__name__}")
            raise TypeError

    @property
    def version_basic(self):
        return self._version_basic

    @version_basic.setter
    def version_basic(self, value):
        if isinstance(value, Version):
            self._version_basic = value

        elif isinstance(value, str):
            try:
                version: Version = Version.from_string(value)

            except TermsInvalidVersionError:
                logger.error("Некорректная структура файла версии")
                raise

            else:
                self._version_basic = version

        else:
            logger.error(f"Значение {value} должно быть типа Version или str, но получено {type(value).__name__}")
            raise TermsInvalidTypeVersionError

    def __bool__(self):
        return self._version == self._version_basic

    def set_version_basic(self):
        if not self._basic_version_file.exists():
            self._version_basic = Version(0, 0, 0)

        else:
            line: str = file_reader(self._basic_version_file, "string")
            self._version_basic = Version.from_string(line)
