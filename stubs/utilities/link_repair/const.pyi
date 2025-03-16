# -*- coding: utf-8 -*-
from enum import Enum
from typing import Any, Iterable
from utilities.common.shared import separator as separator


class FileLanguage(Enum):
    RU = 'russian'
    EN = 'english'
    RU_EN = 'russian+english'


def prepare_logging(items: Iterable[Any] = None, sep: str = None) -> str: ...
