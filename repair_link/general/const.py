# -*- coding: utf-8 -*-
from enum import Enum
from pathlib import Path
from re import Pattern, compile
from typing import NamedTuple, TypeAlias, Any, Iterable


def _version():
    return "1.5.1"


# ---------- General constants ---------- #
StrPath: TypeAlias = str | Path
MD_EXTENSION: str = ".md"
ADOC_EXTENSION: str = ".adoc"
_parent_path: Path = Path.home().joinpath("Desktop")
log_folder: Path = _parent_path.joinpath("_logs/")
result_file_path: Path = Path.cwd().joinpath(f"results.txt")
prog: str = "link_repair"
version: str = f"{prog}, {_version()} prod"
# ---------- General constants ---------- #

# ---------- Patterns ---------- #
_MD_ANCHOR_HEADING: str = r"(?<=\{#)[\w_-]+(?=})"
# noinspection SpellCheckingInspection
_MD_ANCHOR_A_NAME: str = r"(?<=<a\sname=\")[^\"]+(?=\">)"
_MD_ANCHOR_A_ID: str = r"(?<=<a\sid=\")[^\"]+(?=\">)"
_MD_PATTERN_ANCHOR: Pattern = compile(rf"{_MD_ANCHOR_HEADING}|{_MD_ANCHOR_A_NAME}|{_MD_ANCHOR_A_ID}")

_MD_PATTERN_LINK: Pattern = compile(r"\[[^]]+]\(([^)]+)\)")
_MD_PATTERN_INTERNAL_LINK: Pattern = compile(r"\[[^]]+]\(#([^)]+)\)")

_ASCII_DOC_PATTERN_ANCHOR: Pattern = compile(r"(?<=\[[\[#])[^]]+(?=])")
_ASCII_DOC_XREF: Pattern = compile(r"(?<=xref:)[^\[]+(?=\[)")
_ASCII_DOC_LINK: Pattern = compile(r"(?<=link:)[^\[]+(?=\[)")
_ASCII_DOC_IMAGE_INLINE: Pattern = compile(r"(?<=image:)[^\[]+(?=\[)")
_ASCII_DOC_IMAGE_BLOCK: Pattern = compile(r"(?<=image::)[^\[]+(?=\[)")

_ASCII_DOC_PATTERN_LINK: Pattern = compile(
    r"(?<=xref:)[^\[]+(?=\[)|(?<=link:)[^\[]+(?=\[)|(?<=image::)[^\[]+(?=\[)|(?<=image:)[^\[]+(?=\[)"
)
ASCII_DOC_IMAGE: Pattern = compile(r"(?<=image::)[^\[]+(?=\[)|(?<=image:)[^\[]+(?=\[)")
ASCII_DOC_PATTERN_INTERNAL_LINK: Pattern = compile(f"(?<=<<)([^,>]+)[^>]*(?=>>)")
IGNORED_LINKS: tuple[str, ...] = ("http", "mailto", "/", "#")
PATTERN: Pattern = compile(r"(\.\.)(\w)")
# ---------- Patterns ---------- #

separator: str = "-" * 60


class FilePattern(NamedTuple):
    pattern_anchor: Pattern
    pattern_link: Pattern
    pattern_internal_link: Pattern

    def __str__(self):
        return (
            f"ANCHOR: {self.pattern_anchor.pattern}\n"
            f"LINK: {self.pattern_link.pattern}\n"
            f"INTERNAL_LINK: {self.pattern_internal_link.pattern}"
        )

    __repr__ = __str__


md_file_pattern: FilePattern = FilePattern(
    _MD_PATTERN_ANCHOR,
    _MD_PATTERN_LINK,
    _MD_PATTERN_INTERNAL_LINK)

ascii_doc_file_pattern: FilePattern = FilePattern(
    _ASCII_DOC_PATTERN_ANCHOR,
    _ASCII_DOC_PATTERN_LINK,
    ASCII_DOC_PATTERN_INTERNAL_LINK)


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


class Boundary(NamedTuple):
    before: str = ""
    after: str = ""

    def bound(self, value: str):
        return f"{self.before}{value}{self.after}"
