# -*- coding: utf-8 -*-
from glob import iglob
from pathlib import Path
from typing import Iterator, Iterable, Any

from repair_link.general.const import StrPath, ADOC_EXTENSION, MD_EXTENSION
from repair_link.storage.const import with_grandparent, with_parent, unique


class GeneralStorage:
    """
    The storage of the file names.

    Attributes
    ----------
    _root_dir : Path
        The directory path.
    _dirindexes : dict[str, Path]
        The names of the directories with the index.md or the index.adoc file inside.
    _dir_indexes : dict[str, Path]
        The names of the directories with the _index.md or the _index.adoc file inside.
    _non_text_files : dict[str, Path]
        The names of the files having neither the *.md nor the *.adoc extension.
    _text_files : dict[str, Path]
        The names of the markdown and asciidoc files.
    _component_storages : dict[str, ComponentStorage]
        The storages of the 'components' children directories.

    """

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
        """
        Generating the path basing on the root_dir.

        Attributes
        ----------
        path : str or Path
            The path to add to the root_dir.

        Returns
        -------
        Path
            The result path.

        """
        return self._root_dir.joinpath(path).resolve()

    def parent_name(self, path: StrPath) -> str:
        """
        Generating the file parent name.

        Attributes
        ----------
        path : str or Path
            The path to the file.

        """
        return self.join_path(path).parent.name

    def grandparent_name(self, path: StrPath):
        """
        Generating the file grandparent name.

        Attributes
        ----------
        path : str or Path
            The path to the file.

        """
        return self.join_path(path).parent.parent.name

    def prepare(self):
        """
        Generating the dictionaries.

        """
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
        """
        Generating the '_dir_indexes' dictionary.

        Parameters
        ----------
        paths : Iterable[Path]
            The paths to the directories with the '_index.md' or '_index.adoc' file.

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
        """
        Generating the '_dirindexes' dictionary.

        Parameters
        ----------
        paths : Iterable[Path]
            The paths to the directories with the 'index.md' file.

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
        """
        Generating the '_text_files' dictionary.

        Parameters
        ----------
        paths : Iterable[Path]
            The paths to the Markdown files.

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
        """
        Generating the '_non_text_files' dictionary.

        Parameters
        ----------
        paths : Iterable[Path]
            The paths to the non-Markdown and non-AsciiDoc files.

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
        return self._root_dir

    @property
    def _components_path(self) -> Path:
        """
        The path to the 'components' part.

        Returns
        -------
        Path
            The full path to the part.

        """
        return self._root_dir.joinpath("components").resolve()
