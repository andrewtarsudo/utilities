# -*- coding: utf-8 -*-
from enum import Enum
from io import UnsupportedOperation
from pathlib import Path
from typing import Callable, Iterable

from loguru import logger

from utilities.common.constants import StrPath
from utilities.scripts.list_files import list_files_command


class ReaderMode(Enum):
    STRING = "string"
    LINES = "lines"

    def __str__(self):
        return self._value_


def file_reader(path: StrPath, reader_mode: str | ReaderMode):
    if isinstance(reader_mode, str):
        reader_mode: ReaderMode = ReaderMode[reader_mode]

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            functions: dict[ReaderMode, Callable] = {
                ReaderMode.STRING: f.read,
                ReaderMode.LINES: f.readlines}

            _ = functions.get(reader_mode)()

        return _

    except FileNotFoundError:
        input(f"Файл {path} не найден")
        raise

    except PermissionError:
        input(f"Недостаточно прав для записи в файл {path}")
        raise

    except RuntimeError:
        input(f"Истекло время записи в файл {path}")
        raise

    except UnsupportedOperation:
        input(f"Не поддерживаемая операция с файлом {path}")
        raise

    except OSError as e:
        input(f"Ошибка {e.__class__.__name__}: {e.strerror}")
        raise


def get_files(files: Iterable[StrPath] = None, directory: StrPath = None, recursive: bool = True):
    if files is None and directory is None:
        logger.error("Хотя бы один из параметров --file, --dir должен быть задан")
        return None

    if files is None:
        files: list[StrPath] = []

    else:
        files: list[StrPath] = [*files]

    if directory is not None:
        directory: Path = Path(directory)

        listed_files: list[str] = list_files_command(
            directory,
            all_dirs=True,
            extensions="svg",
            prefix="",
            hidden=False,
            recursive=recursive,
            auxiliary=True)

        files.extend(map(directory.joinpath, listed_files))

    return files
