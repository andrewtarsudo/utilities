# -*- coding: utf-8 -*-
from enum import Enum
from pathlib import Path
from typing import NamedTuple
from utilities.common.shared import StrPath

__all__ = ['Link']


class _LinkType(Enum):
    IMAGE_TYPE = 'image'
    TEXT_TYPE = 'text'
    DIR_INDEX_TYPE = 'dir_index'
    DIRINDEX_TYPE = 'dirindex'


class Link(NamedTuple):
    from_file: StrPath
    link_to: str

    def __bool__(self) -> bool: ...

    def origin_destination_path(self) -> Path: ...

    @property
    def anchor(self) -> str | None: ...

    @property
    def stem(self) -> str: ...

    @property
    def parent_stem(self) -> str: ...

    @property
    def grandparent_stem(self) -> str: ...

    @property
    def from_type(self) -> _LinkType: ...

    @property
    def link_to_file(self) -> str: ...

    @property
    def is_component(self) -> bool: ...

    @property
    def component_name(self) -> str | None: ...
