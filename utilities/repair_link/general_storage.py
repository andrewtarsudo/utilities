# -*- coding: utf-8 -*-
from collections import Counter
from glob import iglob
from pathlib import Path
from typing import Iterator, Iterable, Any

from loguru import logger

from utilities.common.constants import ADOC_EXTENSION, MD_EXTENSION, StrPath


def unique(values: Iterable[Any] = None) -> list[Any]:
    """Gets unique values from the iterable instance.

    :param values: The initial iterable. (default = None)
    :type values: Iterable
    :returns: The unique values.
    :rtype: list
    """
    if values is None:
        logger.info("Перечень значений для поиска уникальных пуст")
        return []

    else:
        return [k for k, v in Counter(values).items() if v == 1]


def with_parent(path: StrPath) -> str:
    """Getting the file name with the parent.

    :param path: The file path.
    :type path: str or Path
    :return: The file name.
    :rtype: str
    """
    _: Path = Path(path).parent
    return f"{_.parent.name}/{_.name}"


def with_grandparent(path: StrPath) -> str:
    """Getting the file name with the parent and the grandparent.

    :param path: The file path.
    :type path: str or Path
    :return: The file name.
    :rtype: str
    """
    _: Path = Path(path).parent
    return f"{_.parent.parent.name}/{_.parent.name}/{_.name}"


class GeneralStorage:
    """The storage of the file names."""

    def __init__(self, root_dir: StrPath):
        self._root_dir: Path = Path(root_dir).resolve()
        self._dirindexes: dict[str, Path] = dict()
        self._dir_indexes: dict[str, Path] = dict()
        self._non_text_files: dict[str, Path] = dict()
        self._text_files: dict[str, Path] = dict()
        self._component_storages: dict[str, Any] = dict()

    def __str__(self):
        return f"{self.__class__.__name__}: {self._root_dir}"

    def __repr__(self):
        return f"<{self.__class__.__name__}({self._root_dir})>"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._root_dir == other._root_dir
        elif issubclass(self.__class__, other.__class__) or issubclass(other.__class__, self.__class__):
            return self._root_dir == other.root_dir
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self._root_dir != other._root_dir
        elif issubclass(self.__class__, other.__class__) or issubclass(other.__class__, self.__class__):
            return self._root_dir != other.root_dir
        else:
            return NotImplemented

    def __iter__(self) -> Iterator[Path]:
        return iter(
            [
                *self._dir_indexes.values(),
                *self._dirindexes.values(),
                *self._text_files.values(),
                *self._non_text_files.values()
            ]
        )

    def join_path(self, path: StrPath) -> Path:
        """Generates the path basing on the root_dir.

        :param path: The path to add to the root_dir.
        :type path: str or Path
        """
        return self._root_dir.joinpath(path).resolve()

    def parent_name(self, path: StrPath) -> str:
        """Generates the file parent name.

        :param path: The path to the file.
        :type path: str or Path
        """
        return self.join_path(path).parent.name

    def grandparent_name(self, path: StrPath):
        """Generates the file grandparent name.

        :param path: The path to the file.
        :type path: str or Path
        """
        return self.join_path(path).parent.parent.name

    def prepare(self):
        """Generates the dictionaries."""
        _dir_indexes: list[Path] = []
        _dirindexes: list[Path] = []
        _text_files: list[Path] = []
        _non_md_files: list[Path] = []

        for _ in iglob("**/*.*", root_dir=self._root_dir, recursive=True):
            _path: Path = self.join_path(_)

            if _path.suffix not in (MD_EXTENSION, ADOC_EXTENSION):
                _non_md_files.append(_path)
            elif _path.stem == "_index":
                _dir_indexes.append(_path)
            elif _path.stem == "index":
                _dirindexes.append(_path)
            else:
                _text_files.append(_path)

        self._set_dir_indexes(_dir_indexes)
        self._set_dirindexes(_dirindexes)
        self._set_text_files(_text_files)
        self._set_non_text_files(_non_md_files)
        return

    def _set_dir_indexes(self, paths: Iterable[Path]):
        """Generates the '_dir_indexes' dictionary.

        :param paths: The paths to the directories with the '_index.md' or '_index.adoc' file.
        :type paths: Iterable[Path]
        """
        _unique_md: list[str] = unique(
            iter(
                self.parent_name(_)
                for _ in iglob("**/_index.md", root_dir=self._root_dir, recursive=True)))

        _unique_adoc: list[str] = unique(
            iter(
                self.parent_name(_)
                for _ in iglob("**/_index.adoc", root_dir=self._root_dir, recursive=True)))

        _unique: list[str] = [*_unique_md, *_unique_adoc]

        _unique_parents_md: list[str] = unique(
            iter(
                f"{self.grandparent_name(_)}/{self.parent_name(_)}"
                for _ in iglob("**/_index.md", root_dir=self._root_dir, recursive=True))
        )

        _unique_parents_adoc: list[str] = unique(
            iter(
                f"{self.grandparent_name(_)}/{self.parent_name(_)}"
                for _ in iglob("**/_index.adoc", root_dir=self._root_dir, recursive=True))
        )

        _unique_parents: list[str] = [*_unique_parents_md, *_unique_parents_adoc]

        for _path in paths:
            _name: str = _path.parent.name
            _name_parent: str = with_parent(_path)

            if _name in _unique:
                self._dir_indexes[_name] = self.join_path(_path)

            elif _name_parent in _unique_parents:
                self._dir_indexes[_name_parent] = self.join_path(_path)

            else:
                self._dir_indexes[with_grandparent(_path)] = self.join_path(_path)

        return

    def _set_dirindexes(self, paths: Iterable[Path]):
        """Generates the '_dirindexes' dictionary.

        :param paths: The paths to the directories with the 'index.md' file.
        :type paths: Iterable[Path]
        """
        _unique_md: list[str] = unique(
            iter(
                self.parent_name(_)
                for _ in iglob("**/index.md", root_dir=self._root_dir, recursive=True)))

        _unique_adoc: list[str] = unique(
            iter(
                self.parent_name(_)
                for _ in iglob("**/index.adoc", root_dir=self._root_dir, recursive=True)))

        _unique: list[str] = [*_unique_md, *_unique_adoc]

        _unique_parents_md: list[str] = unique(
            iter(
                f"{self.grandparent_name(_)}/{self.parent_name(_)}"
                for _ in iglob("**/index.md", root_dir=self._root_dir, recursive=True))
        )

        _unique_parents_adoc: list[str] = unique(
            iter(
                f"{self.grandparent_name(_)}/{self.parent_name(_)}"
                for _ in iglob("**/index.adoc", root_dir=self._root_dir, recursive=True))
        )

        _unique_parents: list[str] = [*_unique_parents_md, *_unique_parents_adoc]

        for _path in paths:
            _name: str = _path.parent.name
            _name_parent: str = with_parent(_path)

            if _name in _unique:
                self._dirindexes[_name] = self.join_path(_path)

            elif _name_parent in _unique_parents:
                self._dirindexes[_name_parent] = self.join_path(_path)

            else:
                self._dirindexes[with_grandparent(_path)] = self.join_path(_path)

        return

    def _set_text_files(self, paths: Iterable[Path]):
        """Generates the '_text_files' dictionary.

        :param paths: The paths to the Markdown files.
        :type paths: Iterable[Path]
        """
        _unique_md: list[str] = unique(
            iter(
                self.join_path(_).stem for _ in iglob("**/*.md", root_dir=self._root_dir, recursive=True)
                if not self.join_path(_).stem.endswith("index")))

        _unique_adoc: list[str] = unique(
            iter(
                self.join_path(_).stem for _ in iglob("**/*.adoc", root_dir=self._root_dir, recursive=True)
                if not self.join_path(_).stem.endswith("index")))

        _unique: list[str] = [*_unique_md, *_unique_adoc]

        _unique_parents_md: list[str] = unique(
            iter(
                f"{self.join_path(_).parent.name}/{self.join_path(_).stem}"
                for _ in iglob("**/*.md", root_dir=self._root_dir, recursive=True)
                if not self.join_path(_).stem.endswith("index")))

        _unique_parents_adoc: list[str] = unique(
            iter(
                f"{self.join_path(_).parent.name}/{self.join_path(_).stem}"
                for _ in iglob("**/*.adoc", root_dir=self._root_dir, recursive=True)
                if not self.join_path(_).stem.endswith("index")))

        _unique_parents: list[str] = [*_unique_parents_md, *_unique_parents_adoc]

        for _path in paths:
            _name: str = _path.stem
            _name_parent: str = f"{_path.parent.name}/{_path.stem}"

            if _name in _unique:
                self._text_files[_name] = self.join_path(_path)

            elif _name_parent in _unique_parents:
                self._text_files[_name_parent] = self.join_path(_path)

            else:
                _name_grandparent: str = f"{_path.parent.parent.name}/{_path.parent.name}/{_path.stem}"
                self._text_files[_name_grandparent] = self.join_path(_path)

        return

    def _set_non_text_files(self, paths: Iterable[Path]):
        """Generates the '_non_text_files' dictionary.

        :param paths: The paths to the non-Markdown and non-AsciiDoc files.
        :type paths: Iterable[Path]
        """
        for _path in paths:
            self._non_text_files[_path.name] = self.join_path(_path)

    @property
    def text_files(self):
        return self._text_files

    @property
    def dir_indexes(self):
        return self._dir_indexes

    @property
    def dirindexes(self):
        return self._dirindexes

    @property
    def non_text_files(self):
        return self._non_text_files

    @property
    def root_dir(self):
        """ """
        return self._root_dir

    @property
    def _components_path(self) -> Path:
        """The path to the 'components' part."""
        return self._root_dir.joinpath("components").resolve()


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


class Storage(GeneralStorage):
    """The main storage of all file names."""

    def __init__(self, root_dir: StrPath):
        super().__init__(root_dir)
        self._component_storages: dict[str, ComponentStorage] = dict()

    def prepare(self):
        super().prepare()
        self._set_component_storages()

    @property
    def is_empty(self) -> bool:
        """Checks if the directory does not exist or have _index file in it."""
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

    def get_component_storage(self, name: str) -> ComponentStorage:
        """Gets the ComponentStorage instance by its name.

        :param name: The component storage name.
        :type name: str
        :return: The ComponentStorage instance
        :rtype: ComponentStorage
        """
        if name not in self._component_storage_names:
            logger.debug(f"Component {name} is not found")

        else:
            return self._component_storages.get(name)
