# -*- coding: utf-8 -*-
from enum import Enum
from typing import Any, Iterable

from utilities.common.shared import separator


class FileLanguage(Enum):
    """Class to represent the file language."""
    RU = "russian"
    EN = "english"
    RU_EN = "russian+english"

    def __str__(self):
        return f"{self._value_}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>({self._name_})"


def prepare_logging(items: Iterable[Any] = None, sep: str = None) -> str:
    """Prepares elements for logging.

    :param items: The elements to log.
    :type items: Iterable[Any]
    :param sep: The separator between the log messages.
    :type sep: str
    :return: The line to add to the logger.
    :rtype: str
    """
    if items is None:
        _str_items: str = ""

    else:
        _str_items: str = ",\n".join(map(str, items))

    if sep is None:
        sep: str = separator

    return f"{sep}\n[{_str_items}]\n{sep}"
