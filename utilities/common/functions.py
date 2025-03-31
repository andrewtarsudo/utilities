# -*- coding: utf-8 -*-
from enum import Enum
from io import UnsupportedOperation
from pathlib import Path
from typing import Any, Callable, Iterable

from loguru import logger

from utilities.common.errors import FileReaderError
from utilities.common.shared import StrPath


class ReaderMode(Enum):
    STRING = "string"
    LINES = "lines"

    def __str__(self):
        return self._value_


class FileType(Enum):
    JSON = "json"
    YAML = "yaml"
    NONE = ""

    def initiate(self):
        if self._value_ == "json":
            from json import load as load_file

        elif self._value_ == "yaml":
            from yaml import safe_load as load_file


def file_reader(
    path: StrPath, reader_mode: str | ReaderMode, *, encoding: str = "utf-8"
):
    if isinstance(reader_mode, str):
        reader_mode: ReaderMode = ReaderMode[reader_mode]

    try:
        with open(
            Path(path).expanduser().resolve(), "r", encoding=encoding, errors="ignore"
        ) as f:
            functions: dict[ReaderMode, Callable] = {
                ReaderMode.STRING: f.read,
                ReaderMode.LINES: f.readlines,
            }

            _: str | list[str] = functions.get(reader_mode)()

        return _

    except FileNotFoundError as e:
        logger.error(f"{e.__class__.__name__}: файл {path} не найден")
        raise

    except PermissionError as e:
        from os import stat

        logger.error(
            f"{e.__class__.__name__}: недостаточно прав для чтения файла {path}"
        )
        logger.error(f"Доступ: {stat(path).st_mode}")
        raise

    except RuntimeError as e:
        logger.error(
            f"{e.__class__.__name__}: произошла ошибка обработки во время записи файла {path}"
        )
        raise

    except UnsupportedOperation as e:
        logger.error(
            f"{e.__class__.__name__}: не поддерживаемая операция с файлом {path}: {e.strerror}"
        )
        raise

    except OSError as e:
        logger.error(f"{e.__class__.__name__}: {e.strerror}")
        raise


def file_writer(
    path: StrPath, content: str | Iterable[str], *, encoding: str = "utf-8"
):
    path: Path = Path(path).expanduser().resolve()
    mode: str = "w" if path.exists() else "x"

    if not isinstance(content, str):
        content: str = "".join(content)

    try:
        with open(path, mode=mode, encoding=encoding, errors="ignore") as f:
            f.write(content)

    except PermissionError as e:
        from os import stat

        logger.error(
            f"{e.__class__.__name__}: недостаточно прав для записи в файл {path}"
        )
        logger.error(f"Доступ: {stat(path).st_mode}")
        raise

    except RuntimeError as e:
        logger.error(
            f"{e.__class__.__name__}: произошла ошибка обработки во время записи файла {path}"
        )
        raise

    except UnsupportedOperation as e:
        logger.error(
            f"{e.__class__.__name__}: не поддерживаемая операция с файлом {path}: {e.strerror}"
        )
        raise

    except OSError as e:
        logger.error(f"{e.__class__.__name__}: {e.strerror}")
        raise


def file_reader_type(
    path: StrPath, file_type: str | FileType, *, encoding: str = "utf-8"
):
    if isinstance(file_type, str):
        file_type: ReaderMode = ReaderMode[file_type]

    if file_type is FileType.JSON:
        from json import load as load_file

    elif file_type is FileType.YAML:
        from yaml import safe_load as load_file

    else:
        logger.error("Тип должен быть json или yaml")
        raise FileReaderError

    try:
        with open(path, "r", encoding=encoding, errors="ignore") as f:
            content: dict[str, Any] = load_file(f)

        return content

    except FileNotFoundError as e:
        logger.error(f"{e.__class__.__name__}: файл {path} не найден")
        raise

    except PermissionError as e:
        from os import stat

        logger.error(
            f"{e.__class__.__name__}: недостаточно прав для чтения файла {path}"
        )
        logger.error(f"Доступ: {stat(path).st_mode}")
        raise

    except RuntimeError as e:
        logger.error(
            f"{e.__class__.__name__}: произошла ошибка обработки во время записи файла {path}"
        )
        raise

    except UnsupportedOperation as e:
        logger.error(
            f"{e.__class__.__name__}: не поддерживаемая операция с файлом {path}: {e.strerror}"
        )
        raise

    except OSError as e:
        logger.error(f"{e.__class__.__name__}: {e.strerror}")
        raise
