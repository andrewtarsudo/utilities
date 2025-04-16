# -*- coding: utf-8 -*-
import logging
from logging import basicConfig, Handler, LogRecord
from pathlib import Path
# noinspection PyProtectedMember
from sys import _getframe, stdout as sysout
from types import FrameType
from typing import Any, Literal, NamedTuple, Type
from warnings import simplefilter

from loguru import logger

from utilities.common.shared import DEBUG, NORMAL
from utilities.common.errors import BaseError

HandlerType: Type[str] = Literal["stream", "file_rotating", "result_file"]
LoggingLevel: Type[str] = Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
ColorLevel: Type[str] = Literal["red", "fg #FF7518", "green", "magenta", "light-green", "cyan"]
StyleLevel: Type[str] = Literal["bold", "italic", "underline", "normal"]

__all__ = ["custom_logging"]


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
    LevelColorStyle("CRITICAL", "cyan", "bold"))


class InterceptHandler(Handler):
    """Class to specify the handler to add loggers based on the 'logging' module."""

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
        frame, depth = _getframe(1), 2

        while frame.f_code.co_filename == logging.__file__:
            frame: FrameType = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


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


def _to_result(record: dict) -> bool:
    return record["extra"].get("result") is True


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
    _COLORED_FORMAT: str = " | ".join(
        ("<green>{time:DD-MMM-YYYY HH:mm:ss}</green>::<level>{level.name}</level>",
         "<cyan>{module}</cyan>::<cyan>{function}</cyan>",
         "<cyan>{file.name}</cyan>::<cyan>{name}</cyan>::<cyan>{line}</cyan>",
         "\n<level>{message}</level>"))
    _USER_FORMAT: str = "<level>{message}</level>"

    def __init__(
            self,
            file_name: str,
            handlers: dict[HandlerType, LoggingLevel] = None, *,
            is_debug: bool = False):
        if handlers is None:
            handlers = {}

        self._file_name: str = file_name
        self._handlers: dict[str, str] = handlers
        self._is_debug: bool = is_debug

    @property
    def log_folder(self) -> Path:
        if self._is_debug:
            return DEBUG.parent

        else:
            return NORMAL.parent

    def stream_handler(self) -> dict[str, Any] | None:
        """Specifies the stream handler.

        Handles KeyError.
        """
        try:
            _logging_level: str | None = self._handlers.get("stream")

            return {
                "sink": sysout,
                "level": _logging_level,
                "format": self.__class__._USER_FORMAT,
                "colorize": True,
                "filter": _to_stream,
                "backtrace": False,
                "diagnose": False}

        except KeyError as e:
            print(f"{e.__class__.__name__}, {str(e)}")
            return

    def rotating_file_handler(self) -> dict[str, Any] | None:
        """Specifies the rotating file handler.

        Handles KeyError.
        """
        try:
            _logging_level: str = self._handlers.get("file_rotating", "INFO")
            _log_path: str = str(self.log_folder.joinpath(f"{self._file_name}_{_logging_level.lower()}.log"))

            return {
                "sink": _log_path,
                "level": _logging_level,
                "format": self.__class__._COLORED_FORMAT,
                "colorize": False,
                "diagnose": True,
                "backtrace": True,
                "rotation": "2 MB",
                "mode": "a",
                "encoding": "utf-8",
                "catch": True}

        except KeyError as e:
            print(f"{e.__class__.__name__}, {str(e)}")
            return

    def result_file_handler(self):
        try:
            _logging_level: str = "SUCCESS"
            _log_path: str = Path.cwd().joinpath("results.txt").as_posix()

            return {
                "sink": _log_path,
                "level": _logging_level,
                "format": self.__class__._USER_FORMAT,
                "filter": _to_result,
                "colorize": False,
                "diagnose": True,
                "backtrace": True,
                "mode": "a",
                "encoding": "utf-8",
                "catch": True}

        except KeyError as e:
            print(f"{e.__class__.__name__}, {str(e)}")
            return


def custom_logging(name: str, *, is_debug: bool = False, result_file: bool = False):
    """Specifies the loguru Logger.

    :param name: The log file name.
    :type name: str
    :param is_debug: The flag to use the debug mode.
    :type is_debug: bool, default=False
    :param result_file: Flag to use results.txt file.
    :type result_file: bool, default=False
    """
    if not is_debug:
        simplefilter("ignore")
        stream_level: LoggingLevel = "INFO"

    else:
        stream_level: LoggingLevel = "DEBUG"

    handlers: dict[HandlerType, LoggingLevel] = {
        "stream": stream_level,
        "file_rotating": "DEBUG"}

    file_name: str = name

    # specify the handlers
    logger_configuration: LoggerConfiguration = LoggerConfiguration(file_name, handlers, is_debug=is_debug)
    stream_handler: dict[str, Any] = logger_configuration.stream_handler()
    rotating_file_handler: dict[str, Any] = logger_configuration.rotating_file_handler()

    if result_file:
        result_file_handler: dict[str, Any] = logger_configuration.result_file_handler()
        handlers: list[dict[str, Any]] = [stream_handler, rotating_file_handler, result_file_handler]

    else:
        handlers: list[dict[str, Any]] = [stream_handler, rotating_file_handler]

    logger.configure(handlers=handlers)

    # specify the styles for the levels
    for item in LEVEL_COLOR_STYLE:
        logger.level(name=item.name, color=item.color)

    # add the basic log messages to the logger
    basicConfig(handlers=[InterceptHandler()], level=0)

    logger.catch(level="ERROR", exclude=BaseError, reraise=True)
