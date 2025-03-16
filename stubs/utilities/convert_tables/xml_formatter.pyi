# -*- coding: utf-8 -*-
from enum import Enum
from typing import Iterable
from utilities.convert_tables.qualified_name import fqdn as fqdn
from xml.etree.ElementTree import Element


class Formatting(Enum):
    BOLD = 'bold'
    ITALIC = 'italic'
    SUPERSCRIPT = 'superscript'
    SUBSCRIPT = 'subscript'
    NONE = ''

    @classmethod
    def from_tag(cls, tag: str): ...


def frame_line(line: str, formatting: Iterable[Formatting]) -> str: ...


def find_children(element: Element, tags: Iterable[str] = None) -> set[str] | None: ...


def get_run_text(r: Element) -> dict[str, list[Formatting]]: ...


def get_paragraph_text(p: Element) -> str: ...


def get_all_text(element: Element) -> str: ...
