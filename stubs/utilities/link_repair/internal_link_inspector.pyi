# -*- coding: utf-8 -*-
from utilities.link_repair.file_dict import TextFile

__all__ = ['InternalLinkInspector', 'internal_inspector']


class InternalLinkInspector:
    def __init__(self) -> None: ...

    @property
    def text_file(self) -> TextFile: ...

    def modified_anchor(self, anchor: str) -> str | None: ...

    def inspect_links(self) -> None: ...


internal_inspector: InternalLinkInspector
