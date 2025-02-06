# -*- coding: utf-8 -*-
from enum import Enum
from io import UnsupportedOperation
from pathlib import Path
from typing import Callable, Iterable

from click.core import Context
from click.termui import pause
from loguru import logger

from utilities.common.constants import PRESS_ENTER_KEY, StrPath
from utilities.scripts.list_files import list_files_command


class ReaderMode(Enum):
    STRING = "string"
    LINES = "lines"

    def __str__(self):
        return self._value_


def file_reader(path: StrPath, reader_mode: str | ReaderMode, *, encoding: str = "utf-8"):
    if isinstance(reader_mode, str):
        reader_mode: ReaderMode = ReaderMode[reader_mode]

    try:
        with open(Path(path).expanduser().resolve(), "r", encoding=encoding, errors="ignore") as f:
            functions: dict[ReaderMode, Callable] = {
                ReaderMode.STRING: f.read,
                ReaderMode.LINES: f.readlines}

            _: str | list[str] = functions.get(reader_mode)()

        return _

    except FileNotFoundError:
        input(f"Файл {path} не найден")
        raise

    except PermissionError:
        input(f"Недостаточно прав для чтения файла {path}")
        raise

    except RuntimeError:
        input(f"Истекло время чтения файла {path}")
        raise

    except UnsupportedOperation:
        input(f"Не поддерживаемая операция с файлом {path}")
        raise

    except OSError as e:
        input(f"Ошибка {e.__class__.__name__}: {e.strerror}")
        raise


def file_writer(path: StrPath, content: str | Iterable[str], *, encoding: str = "utf-8"):
    if not isinstance(content, str):
        content: str = "".join(content)

    try:
        with open(path, "w", encoding=encoding, errors="ignore") as f:
            f.write(content)

    except PermissionError:
        logger.error(f"Недостаточно прав для чтения/записи в файл {path}")
        raise

    except RuntimeError:
        input(f"Истекло время чтения файла {path}")
        raise

    except UnsupportedOperation:
        input(f"Не поддерживаемая операция с файлом {path}")
        raise

    except OSError as e:
        input(f"Ошибка {e.__class__.__name__}: {e.strerror}")
        raise


def get_files(
        ctx: Context, *,
        files: Iterable[StrPath] = None,
        directory: StrPath = None,
        recursive: bool = True,
        language: str = "",
        extensions: str = "md adoc"):
    if files is None and directory is None:
        logger.error("Хотя бы один из параметров --file, --dir должен быть задан")
        pause(PRESS_ENTER_KEY)

    if files is None:
        files: list[StrPath] = []

    else:
        files: list[StrPath] = [*files]

    if directory is not None:
        directory: Path = Path(directory).expanduser()

        all_languages: bool = not bool(language)

        listed_files: list[str] = ctx.invoke(
            list_files_command,
            root_dir=directory,
            all_dirs=True,
            all_languages=all_languages,
            language=language,
            extensions=extensions,
            prefix="",
            hidden=False,
            recursive=recursive,
            auxiliary=True)

        files.extend(map(directory.joinpath, listed_files))

    return files
