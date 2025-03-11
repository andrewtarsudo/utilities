# -*- coding: utf-8 -*-
from enum import Enum
from io import UnsupportedOperation
from pathlib import Path
from shutil import rmtree
from typing import Callable, Iterable

from click.core import Context
from click.exceptions import Exit
from click.termui import pause
from click.utils import echo
from loguru import logger

from utilities.common.constants import __version__, DEBUG, NORMAL, PRESS_ENTER_KEY, StrPath


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
        logger.error(f"Файл {path} не найден")
        raise

    except PermissionError:
        from os import stat

        logger.error(f"Недостаточно прав для чтения файла {path}")
        logger.error(f"Доступ: {stat(path).st_mode}")
        raise

    except RuntimeError:
        logger.error(f"Произошла ошибка обработки во время записи файла {path}")
        raise

    except UnsupportedOperation as e:
        logger.error(f"Не поддерживаемая операция с файлом {path}: {e.strerror}")
        raise

    except OSError as e:
        logger.error(f"Ошибка {e.__class__.__name__}: {e.strerror}")
        raise


def file_writer(path: StrPath, content: str | Iterable[str], *, encoding: str = "utf-8"):
    path: Path = Path(path).expanduser().resolve()
    mode: str = "w" if path.exists() else "x"

    if not isinstance(content, str):
        content: str = "".join(content)

    try:
        with open(path, mode=mode, encoding=encoding, errors="ignore") as f:
            f.write(content)

    except PermissionError:
        from os import stat

        logger.error(f"Недостаточно прав для записи в файл {path}")
        logger.error(f"Доступ: {stat(path).st_mode}")
        raise

    except RuntimeError:
        logger.error(f"Произошла ошибка обработки во время записи файла {path}")
        raise

    except UnsupportedOperation as e:
        logger.error(f"Не поддерживаемая операция с файлом {path}: {e.strerror}")
        raise

    except OSError as e:
        logger.error(f"Ошибка {e.__class__.__name__}: {e.strerror}")
        raise


def clear_logs(ctx: Context):
    keep_logs: bool = ctx.obj.get("keep_logs", False)
    debug: bool = ctx.obj.get("debug", False)
    no_result: bool = ctx.obj.get("no_result", False)
    result_file: Path = ctx.obj.get("result_file", None)

    logger.debug(
        f"Версия: {__version__}\n"
        f"Команда: {ctx.command_path}\n"
        f"Параметры: {ctx.params}")

    logger.remove()

    if no_result and result_file is not None:
        result_file.unlink(missing_ok=True)

    if not keep_logs:
        rmtree(NORMAL.parent, ignore_errors=True)

    elif not debug:
        echo(f"Папка с логами: {NORMAL.parent}")

    else:
        echo(f"Папка с логами: {DEBUG.parent}")

    pause(PRESS_ENTER_KEY)
    Exit(0)
