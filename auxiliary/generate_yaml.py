# -*- coding: utf-8 -*-
from pathlib import Path
from frontmatter import load
from mypy.checkpattern import self_match_type_names

from utilities.common.shared import StrPath


class TextFile:
    front_matter: dict[str, str | int | bool]
    root_path: Path

    def __init__(self, path: StrPath):
        self._path = path
        self._front_matter: dict[str, str | int | bool | object] = load(self._path).metadata

    @property
    def weight(self):
        return int(self._front_matter.get("weight"))

    @property
    def draft(self):
        return self._front_matter.get("draft", False)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._path, self.weight == other._path, other.weight

        else:
            return NotImplemented

    def __lt__(self, other):
        if isinstance(other, self.__class__) and not self.draft and not other.draft:
            return self.weight < other.weight

        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, self.__class__) and not self.draft and not other.draft:
            return self.weight <= other.weight

        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, self.__class__) and not self.draft and not other.draft:
            return self.weight > other.weight

        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, self.__class__) and not self.draft and not other.draft:
            return self.weight >= other.weight

        else:
            return NotImplemented

    def __hash__(self):
        return hash(self._path)

