# -*- coding: utf-8 -*-
from enum import Enum
from io import UnsupportedOperation
from pathlib import Path
from shutil import rmtree
from typing import Any, Callable, Iterable, Mapping, Sequence, TypeAlias

from click.core import Context
from click.decorators import pass_context
from click.termui import echo, pause
from loguru import logger
from yaml import safe_load

from utilities.common.errors import FileReaderError

FAIL_COLOR: str = '\033[41m'
PASS_COLOR: str = '\033[42m'
NORMAL_COLOR: str = '\033[0m'

separator: str = "-" * 80

StrPath: TypeAlias = str | Path

DEBUG: Path = Path.cwd().joinpath("_logs/cli_debug.log")
NORMAL: Path = Path("~/Desktop/_logs/cli_debug.log").expanduser().resolve()

PRESS_ENTER_KEY: str = "\nНажмите ENTER, чтобы завершить работу скрипта ..."

HELP: str = """Вывести справочную информацию на экран и завершить работу"""

MD_EXTENSION: str = ".md"
ADOC_EXTENSION: str = ".adoc"

MAX_SYMBOLS: int = 68
MIN_COLUMN = 4

__version__: str = "1.1.3"


class ArgsHelpDict(dict):
    SOURCES: Path = Path(__file__).parent.joinpath("../../sources/dict.yaml")

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


class ReaderMode(Enum):
    STRING = "string"
    LINES = "lines"

    def __str__(self):
        return self._value_


class FileType(Enum):
    JSON = "json"
    YAML = "yaml"
    NONE = ""


def file_reader(path: StrPath, reader_mode: str | ReaderMode, *, encoding: str = "utf-8"):
    """Reads the text file content.

    :param path: The path to the file.
    :type path: str | Path
    :param reader_mode: The type of the result to get.
    :type reader_mode: str | ReaderMode
    :param encoding: The file encoding.
    :type encoding: str
    """
    if isinstance(reader_mode, str):
        reader_mode: ReaderMode = ReaderMode[reader_mode]

    try:
        with open(Path(path).expanduser().resolve(), "r", encoding=encoding, errors="ignore") as f:
            functions: dict[ReaderMode, Callable] = {
                ReaderMode.STRING: f.read,
                ReaderMode.LINES: f.readlines}

            _: str | list[str] = functions.get(reader_mode)()

        return _

    except FileNotFoundError as e:
        logger.error(f"{e.__class__.__name__}: файл {path} не найден")
        raise

    except PermissionError as e:
        from os import stat

        logger.error(f"{e.__class__.__name__}: недостаточно прав для чтения файла {path}")
        logger.error(f"Доступ: {stat(path).st_mode}")
        raise

    except RuntimeError as e:
        logger.error(f"{e.__class__.__name__}: произошла ошибка обработки во время записи файла {path}")
        raise

    except UnsupportedOperation as e:
        logger.error(f"{e.__class__.__name__}: не поддерживаемая операция с файлом {path}: {e.strerror}")
        raise

    except OSError as e:
        logger.error(f"{e.__class__.__name__}: {e.strerror}")
        raise


def file_writer(path: StrPath, content: str | Iterable[str], *, encoding: str = "utf-8"):
    """Writes the text to the file.

    :param path: The path to the file.
    :type path: str | Path
    :param content: The text to write to the file.
    :type content: str | Iterable[str]
    :param encoding: The file encoding.
    :type encoding: str
    """
    path: Path = Path(path).expanduser().resolve()
    mode: str = "w" if path.exists() else "x"

    if not isinstance(content, str):
        content: str = "".join(content)

    try:
        with open(path, mode=mode, encoding=encoding, errors="ignore") as f:
            f.write(content)

    except PermissionError as e:
        from os import stat

        logger.error(f"{e.__class__.__name__}: недостаточно прав для записи в файл {path}")
        logger.error(f"Доступ: {stat(path).st_mode}")
        raise

    except RuntimeError as e:
        logger.error(f"{e.__class__.__name__}: произошла ошибка обработки во время записи файла {path}")
        raise

    except UnsupportedOperation as e:
        logger.error(f"{e.__class__.__name__}: не поддерживаемая операция с файлом {path}: {e.strerror}")
        raise

    except OSError as e:
        logger.error(f"{e.__class__.__name__}: {e.strerror}")
        raise


def file_reader_type(path: StrPath, file_type: str | FileType, *, encoding: str = "utf-8"):
    """Reads the config text file.

    :param path: The path to the file.
    :type path: str | Path
    :param file_type: The file extension.
    :type file_type: str | FileType
    :param encoding: The file encoding.
    :type encoding: str
    """
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

        logger.error(f"{e.__class__.__name__}: недостаточно прав для чтения файла {path}")
        logger.error(f"Доступ: {stat(path).st_mode}")
        raise

    except RuntimeError as e:
        logger.error(f"{e.__class__.__name__}: произошла ошибка обработки во время записи файла {path}")
        raise

    except UnsupportedOperation as e:
        logger.error(f"{e.__class__.__name__}: не поддерживаемая операция с файлом {path}: {e.strerror}")
        raise

    except OSError as e:
        logger.error(f"{e.__class__.__name__}: {e.strerror}")
        raise


@pass_context
def clear_logs(ctx: Context):
    keep_logs: bool = ctx.obj.get("keep_logs", False)
    debug: bool = ctx.obj.get("debug", False)
    no_result: bool = ctx.obj.get("no_result", False)
    result_file: Path = ctx.obj.get("result_file", None)

    logger.debug(
        f"Версия: {__version__}"
        f"\nКоманда: {ctx.command_path}"
        f"\nПараметры: {ctx.params}")

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
    ctx.exit(0)


def _prettify(value: Any):
    return str(value).strip()


def pretty_print(values: Iterable[StrPath] = None):
    if values is None or not values:
        return ""

    else:
        return "\n".join(map(_prettify, values))
