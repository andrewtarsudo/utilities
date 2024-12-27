# -*- coding: utf-8 -*-
from pathlib import Path

from repair_link.general.const import StrPath
from repair_link.storage.general_storage import GeneralStorage


class ComponentStorage(GeneralStorage):
    def __init__(self, root_dir: StrPath, name: str):
        root_dir: Path = Path(root_dir).joinpath("components").joinpath(name)
        super().__init__(root_dir)
        self._name: str = name

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._name == other._name
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self._name != other._name
        else:
            return NotImplemented

    def __contains__(self, item):
        if isinstance(item, StrPath):
            item: Path = Path(item)
            return self._name in item.parents
        else:
            return False
