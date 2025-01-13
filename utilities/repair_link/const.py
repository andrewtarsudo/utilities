# -*- coding: utf-8 -*-
from enum import Enum
from typing import Any, Iterable

from utilities.common.constants import separator

MD_EXTENSION: str = ".md"
ADOC_EXTENSION: str = ".adoc"


class FileLanguage(Enum):
    RU = "russian"
    EN = "english"
    RU_EN = "russian+english"

    def __str__(self):
        return f"{self._value_}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>({self._name_})"


def prepare_logging(items: Iterable[Any] = None, sep: str = None) -> str:
    """
    Internal method to prepare elements for logging.

    Parameters
    ----------
    items : Iterable[Any]
        The elements to log.
    sep : str
        The separator between the log messages.

    Returns
    -------
    str
        The line to add to the logger.

    """
    if items is None:
        _str_items: str = ""

    else:
        _str_items: str = ",\n".join(map(str, items))

    if sep is None:
        sep: str = separator

    return f"{sep}\n[{_str_items}]\n{sep}"
