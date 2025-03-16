# -*- coding: utf-8 -*-

__all__ = ['InternalLinkInspector', 'internal_inspector']


class InternalLinkInspector:
    def __init__(self) -> None: ...

    def modified_anchor(self, anchor: str) -> str | None: ...

    def inspect_links(self) -> None: ...


internal_inspector: InternalLinkInspector
