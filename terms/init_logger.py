# -*- coding: utf-8 -*-
import faulthandler
import os.path as p
# noinspection PyProtectedMember
from logging import currentframe, Handler, LogRecord, basicConfig
from os import getenv
from shutil import rmtree
from sys import stdout as sysout
from types import FrameType
from typing import Type, Literal, Any, Callable, NamedTuple

from loguru import logger

from terms.const import _log_folder

_error_head: str = "".join(("\n", "-" * 79, "\n"))
_error_tail: str = _error_head

HandlerType: Type[str] = Literal["stream", "file_rotating"]
LoggingLevel: Type[str] = Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
ColorLevel: Type[str] = Literal["red", "fg #ffffff", "green", "magenta", "light-green", "cyan"]
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
_OUTPUT_LOGS: bool = getenv("DOCX_MODIFY_LOGS", None) is None

__all__ = ["configure_custom_logging"]


class LevelColorStyle(NamedTuple):
    logging_level: LoggingLevel
    color_level: ColorLevel
    style_level: StyleLevel = "normal"

    def __repr__(self):
        return f"<{self.__class__.__name__}({self._asdict()})>"

    def __str__(self):
        return f"{self.__class__.__name__}: " \
               f"{self.logging_level}, {self.color_level}, {self.style_level}"

    @property
    def name(self) -> str:
        return self.logging_level

    @property
    def color(self) -> str:
        return f"<{self.color_level}><{self.style_level}>"


LEVEL_COLOR_STYLE: tuple[LevelColorStyle, ...] = (
    LevelColorStyle("DEBUG", "light-green"),
    LevelColorStyle("INFO", "fg #ffffff", "italic"),
    LevelColorStyle("SUCCESS", "green", "bold"),
    LevelColorStyle("WARNING", "magenta", "italic"),
    LevelColorStyle("ERROR", "red", "bold"),
    LevelColorStyle("CRITICAL", "cyan", "bold")
)


class InterceptHandler(Handler):
    def emit(self, record: LogRecord):
        # Get corresponding loguru level if exists
        try:
            level: str = logger.level(record.levelname).name
        except ValueError:
            level: int = record.levelno
        import logging
        # Find caller from where originated the logged message
        frame, depth = currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame: FrameType = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _to_stream(record: dict) -> bool:
    if _OUTPUT_LOGS:
        return record["level"].no >= 20
    else:
        return record["level"].no >= 10


def formatter(record: dict) -> str:
    if record["exception"] is not None:
        return "<level>Ошибка при запуске скрипта | {message}\n{exception}</level>\n"

    level_name: str = record["level"].name

    if level_name == "SUCCESS":
        return "<level>{message}</level>\n"

    elif level_name == "ERROR":
        return "<level>%s{message}%s</level>\n" % (_error_head, _error_tail)

    else:
        return "<level>{message}</level>\n"


class LoggerConfiguration:
    def __init__(
            self,
            file_name: str,
            handlers: dict[HandlerType, LoggingLevel] = None):
        if handlers is None:
            handlers = dict()
        self._file_name: str = file_name
        self._handlers: dict[str, str] = handlers

    def stream_handler(self) -> dict[str, Any] | None:
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
        try:
            _logging_level: str = self._handlers.get("file_rotating")
            _log_path: str = str(
                p.join(_log_folder, f"{self._file_name}_{_logging_level.lower()}.log"))
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


def configure_custom_logging(name: str, is_delete: bool = False):
    # enable the faulthandler
    if not faulthandler.is_enabled():
        faulthandler.enable()

    def inner(func: Callable):
        def wrapper(*args, **kwargs):

            stream_level: LoggingLevel | str = "INFO" if _OUTPUT_LOGS else "DEBUG"
            handlers: dict[HandlerType, LoggingLevel | str] | None = {
                "stream": stream_level,
                "file_rotating": "DEBUG"
            }
            file_name: str = name

            # specify the handlers
            logger_configuration: LoggerConfiguration = LoggerConfiguration(file_name, handlers)
            stream_handler: dict[str, Any] = logger_configuration.stream_handler()
            rotating_file_handler: dict[str, Any] = logger_configuration.rotating_file_handler()

            logger.configure(handlers=[stream_handler, rotating_file_handler])

            # specify the styles for the levels
            for item in LEVEL_COLOR_STYLE:
                logger.level(name=item.name, color=item.color)

            # add the basic log messages to the logger
            basicConfig(handlers=[InterceptHandler()], level=0)

            # add the beginning to separate different runs
            logger.success("========================================")
            logger.success(f"Версия: 2.0.0")
            logger.success("Запуск программы")

            return func(*args, **kwargs)

        return wrapper

    # disable faulthandler
    if faulthandler.is_enabled():
        faulthandler.disable()

    # disable loguru logger
    logger.remove()

    # delete the log file and folder
    if is_delete:
        rmtree(_log_folder, True)

    return inner
