# -*- coding: utf-8 -*-
from collections import Counter
from pathlib import Path
from typing import Iterable, Any

from loguru import logger

from repair_link.general.const import StrPath


def unique(values: Iterable[Any] = None) -> list[Any]:
    """Gets unique values from the iterable instance.

    :type values: Iterable, default=None
    :return: The unique values.
    :rtype: list
    """
    if values is None:
        logger.info("Перечень значений для поиска уникальных пуст")
        return []

    else:
        return [k for k, v in Counter(values).items() if v == 1]


def with_parent(path: StrPath) -> str:
    """
    Getting the file name with the parent.

    Parameters
    ----------
    path : str or Path
        The file path.

    Returns
    -------
    str
        The name of the file.

    """
    _: Path = Path(path).parent
    return f"{_.parent.name}/{_.name}"


def with_grandparent(path: StrPath):
    """
    Getting the file name with the parent and the grandparent.

    Parameters
    ----------
    path : str or Path
        The file path.

    Returns
    -------
    str
        The name of the file.

    """
    _: Path = Path(path).parent
    return f"{_.parent.parent.name}/{_.parent.name}/{_.name}"
