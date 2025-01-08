# -*- coding: utf-8 -*-
import os.path as p
from enum import Enum
from io import UnsupportedOperation
from pathlib import Path
from re import Pattern, compile
from sys import platform
from tempfile import gettempdir
from typing import TypeAlias, Iterable

from loguru import logger

StrPath: TypeAlias = str | Path
StrNone: TypeAlias = str | None

path_temp: str = p.dirname(p.dirname(p.abspath(__file__)))
_log_folder: str = p.join(p.expanduser("~"), "Desktop", "_terms_logs")

_TEMPORARY: Path = Path.home().joinpath("local") if platform.startswith("darwin") else Path(gettempdir())
_TEMPORARY_TERMS: Path = _TEMPORARY.joinpath("terms")

_temp_terms: str = f"{_TEMPORARY}{p.sep}terms.adoc"
_temp_version: str = f"{_TEMPORARY}{p.sep}__version__.txt"
_temp_terms_basic: str = f"{_TEMPORARY_TERMS}{p.sep}terms.adoc"
_temp_terms_version: str = f"{_TEMPORARY_TERMS}{p.sep}__version__.txt"

_header_pattern: Pattern = compile(r"\|(.*)\|(.*)\|(.*)\|(.*)\n")

_interceptors: tuple[str, ...] = ("__exit__", "exit", "__quit__", "quit", "!q", "!quit", "!e", "!exit")
separator: str = "".join(("-" * 80, "\n"))


def write_file(file_path: StrPath, content: str | Iterable[str]):
    if isinstance(content, Iterable):
        content: str = "\n".join(content)

    try:
        with open(file_path, "w") as f:
            f.write(content)
            logger.debug(f"File {file_path} is written")

    except FileNotFoundError:
        logger.error(f"Файл {file_path} не найден")
        raise

    except PermissionError:
        logger.error(f"Недостаточно прав для записи в файл {file_path}")
        raise

    except RuntimeError:
        logger.error(f"Истекло время записи в файл {file_path}")
        raise

    except OSError as e:
        logger.debug(f"Ошибка {e.__class__.__name__}: {e.strerror}")
        raise


def read_file(file_path: StrPath) -> str:
    try:
        with open(file_path, "r") as f:
            _: str = f.read()

    except FileNotFoundError:
        logger.error(f"Файл {file_path} не найден")
        raise

    except PermissionError:
        logger.error(f"Недостаточно прав для записи в файл {file_path}")
        raise

    except RuntimeError:
        logger.error(f"Истекло время записи в файл {file_path}")
        raise

    except UnsupportedOperation:
        logger.error(f"Не поддерживаемая операция с файлом {file_path}")
        raise

    except OSError as e:
        logger.error(f"Ошибка {e.__class__.__name__}: {e.strerror}")
        raise

    else:
        logger.debug(f"Файл {file_path} прочитан")
        return _


def read_lines_file(file_path: StrPath) -> list[str]:
    try:
        with open(file_path, "r") as f:
            _: list[str] = f.readlines()

    except FileNotFoundError:
        logger.error(f"Файл {file_path} не найден")
        raise

    except PermissionError:
        logger.error(f"Недостаточно прав для записи в файл {file_path}")
        raise

    except RuntimeError:
        logger.error(f"Истекло время записи в файл {file_path}")
        raise

    except OSError as e:
        logger.error(f"Ошибка {e.__class__.__name__}: {e.strerror}")
        raise

    else:
        logger.error(f"File {file_path} is read")
        return _


class CustomPort(Enum):
    HTTP = 80
    HTTPS = 443

    def __str__(self):
        return f"{self.__class__.__name__}.{self._value_}"

    def __repr__(self):
        return f"<{self.__class__.__name__}.{self._name_}>"


class CustomScheme(Enum):
    HTTP = "http"
    HTTPS = "https"

    def __str__(self):
        return f"{self.__class__.__name__}.{self._value_}"

    def __repr__(self):
        return f"<{self.__class__.__name__}.{self._name_}>"


class State(Enum):
    ACTIVE = "active"
    STOPPED = "stopped"

    def __str__(self):
        return f"{self.__class__.__name__}.{self._value_}"

    def __repr__(self):
        return f"<{self.__class__.__name__}.{self._name_}>"
