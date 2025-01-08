# -*- coding: utf-8 -*-
import faulthandler
import logging
from logging import basicConfig, Handler, LogRecord
from pathlib import Path
# noinspection PyProtectedMember
from sys import _getframe, stdout as sysout
from types import FrameType
from typing import Any, Callable, Literal, NamedTuple, Type
from warnings import simplefilter

from loguru import logger

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
    return record["level"].no >= 10


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
    DEBUG: Path = Path.cwd().joinpath("_logs/translation_api_debug.log")
    NORMAL: Path = Path("~/Desktop/_logs/translation_api_debug.log").expanduser().resolve()
    _COLORED_FORMAT: str = " | ".join(
        ("<green>{time:DD-MMM-YYYY HH:mm:ss}</green>::<level>{level.name}</level>",
         "<cyan>{module}</cyan>::<cyan>{function}</cyan>",
         "<cyan>{file.name}</cyan>::<cyan>{name}</cyan>::<cyan>{line}</cyan>",
         "\n<level>{message}</level>"))
    _USER_FORMAT: str = "{message}\n"

    def __init__(
            self,
            file_name: str,
            handlers: dict[HandlerType, LoggingLevel] = None, *,
            is_debug: bool = False):
        if handlers is None:
            handlers = dict()

        self._file_name: str = file_name
        self._handlers: dict[str, str] = handlers
        self._is_debug: bool = is_debug

    @property
    def log_folder(self) -> Path:
        if self._is_debug:
            return self.__class__.DEBUG.parent
        else:
            return self.__class__.NORMAL.parent

    def stream_handler(self) -> dict[str, Any] | None:
        """
        Specifying the stream handler.

        Handles KeyError."""
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
        """
        Specifying the rotating file handler.

        Handles KeyError."""
        try:
            _logging_level: str = self._handlers.get("file_rotating")
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


def custom_logging(name: str, *, is_debug: bool = False):
    """
    Specifying the logging decorator.

    Parameters
    ----------
    name : str
        The log file name.
    is_debug : bool, default=False
        The flag to use the debug mode.

    """
    if not faulthandler.is_enabled():
        faulthandler.enable()

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

    logger.configure(handlers=[stream_handler, rotating_file_handler])

    # specify the styles for the levels
    for item in LEVEL_COLOR_STYLE:
        logger.level(name=item.name, color=item.color)

    # add the basic log messages to the logger
    basicConfig(handlers=[InterceptHandler()], level=0)

    def inner(func: Callable):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    if faulthandler.is_enabled():
        faulthandler.disable()

    return inner
