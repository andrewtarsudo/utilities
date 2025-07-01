# -*- coding: utf-8 -*-
import logging
from logging import basicConfig, Handler, LogRecord
from pathlib import Path
# noinspection PyProtectedMember
from sys import __stderr__, __stdout__, _getframe
from types import FrameType
from typing import Any, Callable, Literal, NamedTuple, TextIO, Type
from warnings import simplefilter

from loguru import logger

from utilities.common.config_file import config_file
from utilities.common.errors import BaseError, LoggerInitError
from utilities.common.shared import StrPath

HandlerType: Type[str] = Literal["stream", "file_rotating", "result_file"]
LoggingLevel: Type[str] = Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
ColorLevel: Type[str] = Literal["red", "fg #FF7518", "green", "magenta", "light-green", "cyan"]
StyleLevel: Type[str] = Literal["bold", "italic", "underline", "normal"]

COLORED_FORMAT: str = " | ".join(
    ("<green>{time:DD-MMM-YYYY HH:mm:ss}</green>::<level>{level.name}</level>",
     "<cyan>{module}</cyan>::<cyan>{function}</cyan>",
     "<cyan>{file.name}</cyan>::<cyan>{name}</cyan>::<cyan>{line}</cyan>",
     "\n<level>{message}</level>"))
USER_FORMAT: str = "<level>{message}</level>"


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
    min_level: int = 20 if not record["extra"].get("debug") else 10
    max_level: int = 30

    return (
            min_level <= record["level"].no < max_level
            and record["name"] != "logging"
            and not record["extra"].get("suppress", False))


def _to_stderr(record: dict) -> bool:
    return record["level"].no >= 30


def _to_result(record: dict) -> bool:
    return record["extra"].get("result") is True


def set_handler(handler_type: HandlerType, **kwargs):
    match handler_type:
        case "stream":
            handler: dict[str, TextIO | StrPath | bool | Callable] = {
                "colorize": True,
                "backtrace": False,
                "diagnose": False}

        case "file_rotating":
            handler: dict[str, TextIO | StrPath | bool | Callable] = {
                "colorize": False,
                "diagnose": True,
                "backtrace": True,
                "rotation": "2 MB",
                "mode": "w",
                "encoding": "utf-8",
                "catch": True}

        case "result_file":
            handler: dict[str, TextIO | StrPath | bool | Callable] = {
                "colorize": False,
                "diagnose": False,
                "backtrace": False,
                "mode": "w",
                "encoding": "utf-8",
                "catch": False}

        case _:
            raise LoggerInitError

    handler.update(**kwargs)
    return handler


def stream_handler(level: LoggingLevel = "INFO") -> dict[str, Any] | None:
    """Specifies the stream handler.

    Handles KeyError.
    """
    kwargs: dict[str, TextIO | str | Callable | bool] = {
        "sink": __stdout__,
        "level": level,
        "format": USER_FORMAT,
        "filter": _to_stream}

    return set_handler("stream", **kwargs)


def stderr_handler(level: LoggingLevel = "WARNING") -> dict[str, Any] | None:
    """Specifies the stream handler."""
    kwargs: dict[str, TextIO | str | Callable | bool] = {
        "sink": __stderr__,
        "level": level,
        "format": USER_FORMAT,
        "filter": _to_stderr,
        "diagnose": True}

    return set_handler("stream", **kwargs)


def rotating_file_handler(sink: str = None) -> dict[str, Any] | None:
    """Specifies the rotating file handler."""
    level: LoggingLevel = "DEBUG"

    if sink is None:
        sink: str = (
            Path(config_file.get_general("log_path"))
            .expanduser()
            .resolve()
            .joinpath(f"utilities_{level.lower()}.log")
            .as_posix())

    kwargs: dict[str, StrPath] = {
        "level": level,
        "sink": sink,
        "format": COLORED_FORMAT}

    return set_handler("file_rotating", **kwargs)


def result_file_handler(sink: str = None):
    level: LoggingLevel = "SUCCESS"

    if sink is None:
        sink: str = Path.cwd().joinpath("results.txt").as_posix()

    kwargs: dict[str, StrPath | Callable] = {
        "sink": sink,
        "level": level,
        "format": USER_FORMAT,
        "filter": _to_result}

    return set_handler("result_file", **kwargs)


def custom_logging(*, is_debug: bool = False, result_file: bool = False):
    """Specifies the loguru Logger.

    :param is_debug: The flag to use the debug mode.
    :type is_debug: bool, default=False
    :param result_file: Flag to use results.txt file.
    :type result_file: bool, default=False
    """
    logger.remove()

    if not is_debug:
        simplefilter("ignore")
        stream_level: LoggingLevel = "INFO"

    else:
        stream_level: LoggingLevel = "DEBUG"

    handlers: list[dict[str, Any]] = [stream_handler(stream_level), stderr_handler(), rotating_file_handler()]

    if result_file:
        handlers.append(result_file_handler())

    logger.configure(handlers=handlers)

    logger.disable("httpx")
    logger.disable("httpcore")

    # specify the styles for the levels
    for item in LEVEL_COLOR_STYLE:
        logger.level(name=item.name, color=item.color)

    # add the basic log messages to the logger
    basicConfig(handlers=[InterceptHandler()], level=0)

    logger.catch(level="DEBUG", exclude=BaseError, reraise=False)


def add_handler(handler_type: HandlerType, **kwargs):
    handler: dict[str, Any] = set_handler(handler_type, **kwargs)
    logger.add(**handler)
