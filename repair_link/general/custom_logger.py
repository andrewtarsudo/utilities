# -*- coding: utf-8 -*-
import faulthandler
import logging
from logging import Handler, LogRecord
from shutil import rmtree
from sys import stdout as sysout
from types import FrameType
from typing import Any, Callable, Literal, Type, NamedTuple

from loguru import logger

from repair_link.general.const import log_folder, result_file_path, version

# ---------- General constants ---------- #
_error_head: str = "---------- Не исправлено автоматически ----------\n"
_error_tail: str = "\n-------------------------------------------------\n"
_warning_head: str = "!  "
_warning_tail: str = "  !\n"
_critical_head: str = "-------------------------------------------------"
_critical_tail: str = "-------------------------------------------------"
# ---------- General constants ---------- #


HandlerType: Type[str] = Literal["stream", "file_rotating", "result_file"]
LoggingLevel: Type[str] = Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
ColorLevel: Type[str] = Literal["red", "fg #FF7518", "green", "magenta", "light-green", "cyan"]
StyleLevel: Type[str] = Literal["bold", "italic", "underline", "normal"]

_WB_FORMAT: str = " | ".join(
    ("{time:DD-MMM-YYYY HH:mm:ss}::{level.name}",
     "{module}::{function}",
     "{file.name}::{name}::{line}",
     "\n{message}")
)
_COLORED_FORMAT: str = " | ".join(
    ("<green>{time:DD-MMM-YYYY HH:mm:ss}</green>::<level>{level.name}</level>",
     "<cyan>{module}</cyan>::<cyan>{function}</cyan>",
     "<cyan>{file.name}</cyan>::<cyan>{name}</cyan>::<cyan>{line}</cyan>",
     "\n<level>{message}</level>")
)
_USER_FORMAT: str = "{message}\n"

__all__ = ["configure_custom_logging"]


class LevelColorStyle(NamedTuple):
    # noinspection PyUnresolvedReferences
    """
    The instance to gather the logging level, the color and the style of the level.

    Attributes
    ----------
    logging_level : LoggingLevel
        The minimum level to log.
    color_level : ColorLevel
        The color of the text.
    style_level : StyleLevel
        The style of the text.

    """
    logging_level: LoggingLevel
    color_level: ColorLevel
    style_level: StyleLevel = "normal"

    def __repr__(self):
        return f"<{self.__class__.__name__}({self._asdict()})>"

    def __str__(self):
        return f"{self.__class__.__name__}: {self.logging_level}, {self.color_level}, {self.style_level}"

    @property
    def name(self) -> str:
        """
        The alias for the 'logging_level' property.

        """
        return self.logging_level

    @property
    def color(self) -> str:
        """
        The value to specify the text style.

        Returns
        -------
        str
            The message text style.

        """
        return f"<{self.color_level}><{self.style_level}>"


LEVEL_COLOR_STYLE: tuple[LevelColorStyle, ...] = (
    LevelColorStyle("DEBUG", "light-green"),
    LevelColorStyle("INFO", "fg #FF7518", "italic"),
    LevelColorStyle("SUCCESS", "green", "bold"),
    LevelColorStyle("WARNING", "magenta", "italic"),
    LevelColorStyle("ERROR", "red", "bold"),
    LevelColorStyle("CRITICAL", "cyan", "bold")
)


class InterceptHandler(Handler):
    """
    The handler to add loggers based on the 'logging' module.

    """

    def emit(self, record: LogRecord):
        """
        Adding the messages to the logger.

        Parameters
        ----------
        record : LogRecord
            The message to add.

        """
        # Get corresponding loguru level if exists
        try:
            level: str = logger.level(record.levelname).name

        except ValueError:
            level: int = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2

        while frame.f_code.co_filename == logging.__file__:
            frame: FrameType = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _to_result(record: dict) -> bool:
    """
    The filter to add for the 'results.txt' file.

    Parameters
    ----------
    record : dict
        The message of the logger.

    Returns
    -------
    bool
        The check result for the message.

    """
    return "result" in record["extra"]


def _to_stream(record: dict) -> bool:
    """
    The filter to add for the console output.

    Parameters
    ----------
    record : dict
        The message of the logger.

    Returns
    -------
    bool
        The check result for the message.

    """
    return record["level"].no >= 20


def formatter(record: dict) -> str:
    """
    The formatter for the logger messages.

    Parameters
    ----------
    record : dict
        The message of the logger.

    Returns
    -------
    str
        The formatted message.

    """
    if record["exception"] is not None:
        return "<level>Ошибка при запуске скрипта | {message}\n{exception}</level>\n"

    level_name: str = record["level"].name

    if level_name == "SUCCESS":
        return "<level>::Изменено::{message}</level>\n"

    elif level_name == "WARNING":
        return "<level>%s{message}%s</level>\n" % (_warning_head, _warning_tail)

    elif level_name == "ERROR":
        return "<level>%s{message}%s</level>\n" % (_error_head, _error_tail)

    else:
        return "<level>{message}</level>\n"


class LoggerConfiguration:
    """
    The loguru logger configuration instance.

    Attributes
    ----------
    _file_name : str
        The name of the log file.
    _handlers : dict[str, str]
        The logger handlers.

    """

    def __init__(
            self,
            file_name: str,
            handlers: dict[HandlerType, LoggingLevel] = None):
        if handlers is None:
            handlers = dict()

        self._file_name: str = file_name
        self._handlers: dict[str, str] = handlers

    def stream_handler(self) -> dict[str, Any] | None:
        """
        Specifying the stream handler.

        Handles KeyError.

        """
        try:
            _logging_level: str | None = self._handlers.get("stream")

            return {
                "sink": sysout,
                "level": _logging_level,
                "format": formatter,
                "colorize": True,
                "filter": _to_stream,
                "backtrace": False,
                "diagnose": False
            }

        except KeyError as exc:
            print(f"{exc.__class__.__name__}, {str(exc)}")
            return

    def rotating_file_handler(self) -> dict[str, Any] | None:
        """
        Specifying the rotating file handler.

        Handles KeyError.

        """
        try:
            _logging_level: str = self._handlers.get("file_rotating")
            _log_path: str = str(log_folder.joinpath(f"{self._file_name}_{_logging_level.lower()}.log"))

            return {
                "sink": _log_path,
                "level": _logging_level,
                "format": _WB_FORMAT,
                "colorize": False,
                "diagnose": True,
                "backtrace": True,
                "rotation": "2 MB",
                "mode": "a",
                "encoding": "utf-8",
                "catch": True
            }

        except KeyError as exc:
            print(f"{exc.__class__.__name__}, {str(exc)}")
            return

    def result_file_handler(self) -> dict[str, Any] | None:
        """
        Specifying the 'results.txt' file handler.

        Handles KeyError.

        """
        try:
            _logging_level: str = self._handlers.get("result_file")
            return {
                "sink": str(result_file_path),
                "level": _logging_level,
                "format": _USER_FORMAT,
                "filter": _to_result,
                "colorize": False,
                "diagnose": False,
                "backtrace": False,
                "mode": "w",
                "encoding": "utf-8"
            }

        except KeyError as exc:
            print(f"{exc.__class__.__name__}, {str(exc)}")
            return


def configure_custom_logging(name: str, *, is_delete: bool = False, is_initial: bool = True):
    """
    Specifying the logging decorator.

    Parameters
    ----------
    name : str
        The log file name.
    is_delete : bool, default=False
        The flag to delete the log file and log folder.
    is_initial : bool, default=True
        The flag to add the initial lines.

    """
    # enable the faulthandler
    if not faulthandler.is_enabled():
        faulthandler.enable()

    def inner(func: Callable):
        def wrapper(*args, **kwargs):
            handlers: dict[HandlerType, LoggingLevel] = {
                "stream": "INFO",
                "file_rotating": "DEBUG",
                "result_file": "INFO"
            }

            file_name: str = name

            # specify the handlers
            logger_configuration: LoggerConfiguration = LoggerConfiguration(file_name, handlers)
            stream_handler: dict[str, Any] = logger_configuration.stream_handler()
            rotating_file_handler: dict[str, Any] = logger_configuration.rotating_file_handler()
            result_file_handler: dict[str, Any] = logger_configuration.result_file_handler()

            logger.configure(handlers=[stream_handler, rotating_file_handler, result_file_handler])

            # specify the styles for the levels
            for item in LEVEL_COLOR_STYLE:
                logger.level(name=item.name, color=item.color)

            # add the basic log messages to the logger
            logging.basicConfig(handlers=[InterceptHandler()], level=0)

            if is_initial is True:
                # add the beginning to separate different runs
                logger.info("========================================")
                logger.info(f"Версия: {version}")
                logger.info("Запуск программы:")

            return func(*args, **kwargs)

        return wrapper

    if faulthandler.is_enabled():
        faulthandler.disable()

    # delete the log file and folder
    if is_delete:
        rmtree(log_folder, True)

    return inner
