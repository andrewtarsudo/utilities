# -*- coding: utf-8 -*-
from click.core import Context as Context
from enum import Enum
from typing import Iterable
from utilities.common.shared import DEBUG as DEBUG, NORMAL as NORMAL, PRESS_ENTER_KEY as PRESS_ENTER_KEY, \
    StrPath as StrPath, __version__ as __version__


class ReaderMode(Enum):
    STRING = 'string'
    LINES = 'lines'


def file_reader(path: StrPath, reader_mode: str | ReaderMode, *, encoding: str = 'utf-8'): ...


def file_writer(path: StrPath, content: str | Iterable[str], *, encoding: str = 'utf-8'): ...


def clear_logs(ctx: Context): ...
