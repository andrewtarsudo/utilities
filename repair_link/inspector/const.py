# -*- coding: utf-8 -*-
from itertools import chain, product
from pathlib import Path

from repair_link.general.const import MD_EXTENSION, ADOC_EXTENSION, StrPath


def _prepare_link(link: str) -> str:
    """
    The generation of the link to the file without index/_index and extension.

    Parameters
    ----------
    link : str
        The link to the file.

    Returns
    -------
    str
        The modified link according to the rules.
    """
    _: str = link.removesuffix("/")

    names: tuple[str, ...] = ("_index", "index", "")
    suffixes: tuple[str, ...] = (MD_EXTENSION, ADOC_EXTENSION)

    for name, suffix in product(names, suffixes):
        item: str = f"{name}{suffix}"

        if _.endswith(item):
            _ = _.removesuffix(item)

    return _


def _update_prefix(*lines: str) -> tuple[str, ...]:
    """
    The generation of the links having one more or less level ups.

    Parameters
    ----------
    lines : str
        The links to modify.

    Returns
    -------
    tuple[str, ...]

    """
    return tuple(chain.from_iterable((f"../{_}", _, _.removeprefix("../")) for _ in lines))


def _update_suffix(*lines: str) -> tuple[str, ...]:
    """
    The generation of the full path to the file.

    Parameters
    ----------
    lines : str
        The links to modify.

    Returns
    -------
    tuple[str, ...]

    """
    return tuple(
        chain.from_iterable(
            (
                _,
                f"{_}{MD_EXTENSION}",
                f"{_}/index{MD_EXTENSION}",
                f"{_}/_index{MD_EXTENSION}",
                f"{_}/index.en{MD_EXTENSION}",
                f"{_}/_index.en{MD_EXTENSION}",
                f"{_}{ADOC_EXTENSION}",
                f"{_}/index{ADOC_EXTENSION}",
                f"{_}/_index{ADOC_EXTENSION}",
                f"{_}/index.en{ADOC_EXTENSION}",
                f"{_}/_index.en{ADOC_EXTENSION}",
            ) for _ in lines))


def get_options(path: StrPath) -> tuple[str, ...]:
    """
    The generation of the all trivial links that are possible to be valid based on the given one.

    Parameters
    ----------
    path : str or Path
        The link to the file.

    Returns
    -------
    tuple[str, ...]
        The full set of links to inspect.

    """
    _: str = f"{path}".removeprefix('./')
    return _update_suffix(*_update_prefix(f"{path}"))


def validate_file_path(path: StrPath) -> bool:
    """
    The validation of the file path.

    Parameters
    ----------
    path : str or Path
        The path to inspect.

    Returns
    -------
    bool
        The result of the check.

    """
    _: Path = Path(path).resolve()
    return _.exists() and _.is_file()
