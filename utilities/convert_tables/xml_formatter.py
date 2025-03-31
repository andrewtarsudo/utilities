# -*- coding: utf-8 -*-
from enum import Enum
from typing import Iterable

from xml.etree.ElementTree import Element

from utilities.convert_tables.qualified_name import _ns, fqdn


class Formatting(Enum):
    BOLD = "bold"
    ITALIC = "italic"
    SUPERSCRIPT = "superscript"
    SUBSCRIPT = "subscript"
    NONE = ""

    def __repr__(self):
        return f"{self.__class__.__name__}: {self._value_}"

    __str__ = __repr__

    @classmethod
    def from_tag(cls, tag: str):
        _conversion_dict: dict[str, str] = {
            fqdn("w:b"): "bold",
            fqdn("w:i"): "italic",
            fqdn("superscript"): "superscript",
            fqdn("subscript"): "subscript"}
        return cls(_conversion_dict.get(tag))


def frame_line(line: str, formatting: Iterable[Formatting]) -> str:
    formatting_dict: dict[Formatting, tuple[str, str]] = {
        Formatting.BOLD: ("**", "**"),
        Formatting.ITALIC: ("_", "_"),
        Formatting.SUPERSCRIPT: ("<sup>", "</sup>"),
        Formatting.SUBSCRIPT: ("<sub>", "</sub>"),
        Formatting.NONE: ("", "")}

    for _format in formatting:
        prefix, suffix = formatting_dict.get(_format)
        line: str = f"{prefix}{line}{suffix}"

    return line


def find_children(element: Element, tags: Iterable[str] = None) -> set[str] | None:
    if tags is None:
        return

    child: Element
    _children_names: set[str] = {child.tag for child in iter(element)}
    return _children_names.intersection(tags)


def get_run_text(r: Element) -> dict[str, list[Formatting]]:
    tags: tuple[str, ...] = (fqdn("w:b"), fqdn("w:i"), fqdn("w:vertAlign"))
    r_pr: Element | None = r.find(fqdn("w:rPr"), _ns)
    t: Element | None = r.find(fqdn("w:t"), _ns)
    text: str = t.text if t is not None else ""

    if r_pr is None:
        return {text: Formatting.NONE}

    _formats: list[str] = [*find_children(r_pr, tags)]

    if fqdn("w:vertAlign") in _formats:
        vert_align: Element = r_pr.find(fqdn("w:vertAlign"), _ns)
        w_val: str = vert_align.get(fqdn("w:val"))

        if w_val != "baseline":
            _formats.append(w_val)

        _formats.remove(fqdn("w:vertAlign"))

    if not _formats:
        return {text: [Formatting.NONE]}

    else:
        return {text: [Formatting.from_tag(_format) for _format in _formats]}


def get_paragraph_text(p: Element) -> str:
    r: Element
    lines: list[str] = [
        frame_line(k, v)
        for r in p.findall(fqdn("w:r"), _ns)
        for k, v in get_run_text(r).items()]

    return "".join(lines)


def get_all_text(element: Element) -> str:
    return "<br>".join(
        get_paragraph_text(p)
        for p in element.findall(fqdn("w:p"), _ns))
