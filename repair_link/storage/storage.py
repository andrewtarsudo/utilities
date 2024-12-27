# -*- coding: utf-8 -*-
from pathlib import Path

from loguru import logger

from repair_link.general.const import StrPath, MD_EXTENSION, ADOC_EXTENSION
from repair_link.storage.component_storage import ComponentStorage
from repair_link.storage.general_storage import GeneralStorage


class Storage(GeneralStorage):
    """
    The main storage of all file names.

    Attributes
    ----------
    _root_dir : Path
        The directory path.
    _dirindexes : dict[str, Path]
        The names of the directories with the index.md or index.adoc file inside.
    _dir_indexes : dict[str, Path]
        The names of the directories with the _index.md or _index.adoc file inside.
    _non_text_files : dict[str, Path]
        The names of the files having neither the *.md nor the *.adoc extension.
    _text_files : dict[str, Path]
        The names of the markdown or adoc files.
    _component_storages : dict[str, ComponentStorage]
        The storages for the components.

    """

    def __init__(self, root_dir: StrPath):
        super().__init__(root_dir)
        self._component_storages: dict[str, ComponentStorage] = dict()

    def prepare(self):
        super().prepare()
        self._set_component_storages()

    @property
    def is_empty(self) -> bool:
        """
        The flag of having the 'components' directory and any files in it.

        Returns
        -------
        bool
            True if the directory does not exist or have _index file, otherwise, False.

        """
        if not self._components_path.exists():
            return True
        else:
            bool_md: bool = self._components_path.joinpath(f"_index{MD_EXTENSION}").exists()
            bool_asciidoc: bool = self._components_path.joinpath(f"_index{ADOC_EXTENSION}").exists()
            return not (bool_md or bool_asciidoc)

    @property
    def _component_storage_names(self):
        if self.is_empty:
            logger.debug(
                f"Directory {self._root_dir} has no 'components' directory\n"
                f"Processing ComponentStorage items is skipped")
            return []
        else:
            return [item.name for item in self._components_path.iterdir() if item.is_dir()]

    def _set_component_storages(self):
        for _name in self._component_storage_names:
            component_storage: ComponentStorage = ComponentStorage(self._root_dir, _name)
            component_storage.prepare()
            self._component_storages[_name] = component_storage
        return

    def get_component_storage(self, name: str):
        if name not in self._component_storage_names:
            logger.debug(f"Component {name} is not found")
        else:
            return self._component_storages.get(name)
