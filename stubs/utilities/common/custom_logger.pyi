# -*- coding: utf-8 -*-
from logging import Handler, LogRecord
from pathlib import Path
from typing import Any, Literal, NamedTuple, Type

HandlerType: Type[str] = Literal["stream", "file_rotating", "result_file"]
LoggingLevel: Type[str] = Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
ColorLevel: Type[str] = Literal["red", "fg #FF7518", "green", "magenta", "light-green", "cyan"]
StyleLevel: Type[str] = Literal["bold", "italic", "underline", "normal"]

__all__ = ['custom_logging']


class LevelColorStyle(NamedTuple):
    logging_level: LoggingLevel
    color_level: ColorLevel
    style_level: StyleLevel = ...

    @property
    def name(self) -> str: ...

    @property
    def color(self) -> str: ...


class InterceptHandler(Handler):
    def emit(self, record: LogRecord): ...


class LoggerConfiguration:
    def __init__(self, file_name: str, handlers: dict[HandlerType, LoggingLevel] = None, *,
                 is_debug: bool = False) -> None: ...

    @property
    def log_folder(self) -> Path: ...

    def stream_handler(self) -> dict[str, Any] | None: ...

    def rotating_file_handler(self) -> dict[str, Any] | None: ...

    def result_file_handler(self): ...


def custom_logging(name: str, *, is_debug: bool = False, result_file: bool = False): ...
