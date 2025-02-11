# -*- coding: utf-8 -*-
from itertools import chain, product
from os.path import relpath
from pathlib import Path

from loguru import logger

from utilities.common.constants import ADOC_EXTENSION, MD_EXTENSION, StrPath
from utilities.link_repair.file_dict import FileDict, TextFile, DirFile
from utilities.link_repair.link import Link
from utilities.link_repair.internal_link_inspector import internal_inspector, InternalLinkInspector
from utilities.link_repair.general_storage import GeneralStorage, ComponentStorage, Storage


def _prepare_link(link: str) -> str:
    """
    The generation of the link to the file without index/_index and extension.

    Parameters
    ----------
    link : str
        The link to the file.

    Returns
    -------
    str
        The modified link according to the rules.
    """
    _: str = link.removesuffix("/")

    names: tuple[str, ...] = ("_index", "index", "")
    suffixes: tuple[str, ...] = (MD_EXTENSION, ADOC_EXTENSION)

    for name, suffix in product(names, suffixes):
        item: str = f"{name}{suffix}"

        if _.endswith(item):
            _: str = _.removesuffix(item)

    return _


def _update_prefix(*lines: str) -> tuple[str, ...]:
    """
    The generation of the links having two more or less level ups.

    Parameters
    ----------
    lines : str
        The links to modify.

    Returns
    -------
    tuple[str, ...]

    """
    return tuple(
        chain.from_iterable(
            (
                f"../../{_}",
                f"../{_}",
                _,
                _.removeprefix("../"),
                _.removeprefix("../../")
            ) for _ in lines))


def _update_suffix(*lines: str) -> tuple[str, ...]:
    """
    The generation of the full path to the file.

    Parameters
    ----------
    lines : str
        The links to modify.

    Returns
    -------
    tuple[str, ...]

    """
    return tuple(
        chain.from_iterable(
            (
                _,
                f"{_}{MD_EXTENSION}",
                f"{_}/index{MD_EXTENSION}",
                f"{_}/_index{MD_EXTENSION}",
                f"{_}/index.en{MD_EXTENSION}",
                f"{_}/_index.en{MD_EXTENSION}",
                f"{_}{ADOC_EXTENSION}",
                f"{_}/index{ADOC_EXTENSION}",
                f"{_}/_index{ADOC_EXTENSION}",
                f"{_}/index.en{ADOC_EXTENSION}",
                f"{_}/_index.en{ADOC_EXTENSION}",
            ) for _ in lines))


def get_options(path: StrPath) -> tuple[str, ...]:
    """
    The generation of the all trivial links that are possible to be valid based on the given one.

    Parameters
    ----------
    path : str or Path
        The link to the file.

    Returns
    -------
    tuple[str, ...]
        The full set of links to inspect.

    """
    _: str = f"{path}".removeprefix('./')
    return _update_suffix(*_update_prefix(f"{path}"))


def validate_file_path(path: StrPath) -> bool:
    """
    The validation of the file path.

    Parameters
    ----------
    path : str or Path
        The path to inspect.

    Returns
    -------
    bool
        The result of the check.

    """
    _: Path = Path(path).resolve()
    return _.exists() and _.is_file()


class LinkInspector:
    """
    Class to represent the entity to inspect the link.

    Attributes
    ----------
    _storage : Storage
        The entity to store the information about the directory content.
    _link : Link
        The link to validate.
    _destination : Path
        The path to the file pointed in the link.
    _proper_link : str or None
        The proper link that must be in the file.
    _proper_anchor : str or None
        The proper anchor that must be in the file.
    _file_dict : FileDict
        The entity to store the processed files.
    _internal_inspector : InternalLinkInspector
        The entity to inspect anchors.

    """
    updated_anchors: set[str] = set()

    def __init__(
            self,
            storage: Storage | None = None,
            file_dict: FileDict | None = None):
        self._storage: Storage | None = storage
        self._file_dict: FileDict | None = file_dict
        self._link: Link | None = None
        self._destination: Path | None = None
        self._proper_link: str | None = None
        self._proper_anchor: str | None = None
        self._internal_inspector: InternalLinkInspector = internal_inspector

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __bool__(self):
        """
        The validation if the destination file has already been found.

        """
        return self._destination is not None

    def preprocess_link(self):
        _: str | None = self._link.anchor
        _updated_anchor: str = Path(self._link.link_to_file).stem.removeprefix('_').replace('_', '-')

        if _ is not None and _ in self.updated_anchors:
            _indexes: list[int] = self.source_file().find_anchor(_)
            self.source_file().update_line(_indexes, _, f"{_}-{_updated_anchor}", is_boundary=True)

    def base_dir(self) -> Path:
        """
        The base path to get relative links.

        """
        return self._storage.root_dir.parent.parent

    def source_link(self) -> Path:
        """
        The path to the file containing the link.

        """
        return Path(self._link.from_file)

    def source_file(self) -> TextFile:
        return self._file_dict.get(self.source_link())

    def destination_file(self) -> DirFile | TextFile:
        """
        The file given in the link if found.

        """
        if not self._link.is_component:
            return self._file_dict.get(self._destination) if bool(self) else None

    def inspect_original_link(self):
        """
        The validation of the original link.

        """
        _options: list[str] = [*_update_suffix(f"{self._link.origin_destination_path()}")]

        for index, _option in enumerate(_options):
            if validate_file_path(_option):
                logger.debug(f"Success, link = {_option}")
                self._destination = Path(_option)
                self._proper_link = self._link.link_to
                return

        else:
            logger.debug("Fail, link is invalid")
            return

    def inspect_trivial_options(self):
        """
        The validation if the link has an invalid number of level ups.

        """
        if bool(self):
            logger.debug("File path has already been found")
            return

        for index, _option in enumerate(get_options(self._link.link_to_file)):
            _: Path = self._link.from_file.joinpath(_option).resolve()

            if validate_file_path(_):
                logger.debug(f"Success, option = {_}")
                self._destination = _
                return

        else:
            logger.debug("None of the most possible paths leads to the file")
            return

    def find_in_storage(self, storage: GeneralStorage):
        if bool(self):
            logger.debug("File path has already been found")
            return

        _storage_dict_items: tuple[dict[str, Path], ...] = (
            storage.dir_indexes,
            storage.dirindexes,
            storage.non_text_files,
            storage.text_files
        )

        for _storage_dict in _storage_dict_items:
            for _name in self._names():
                if _name in _storage_dict.keys():
                    self._destination = _storage_dict.get(_name)
                    return

        else:
            logger.debug(f"missing file = {self._link.link_to}")
            return

    def find_file(self):
        """
        The file given in the link by its name from the file name storage.

        """
        self.find_in_storage(self._storage)

        if self._link.component_name is not None:
            _component_storage: ComponentStorage = self._storage.get_component_storage(self._link.component_name)
            logger.debug(f"_component_storage = {_component_storage}")
            self.find_in_storage(_component_storage)

    @property
    def storage(self) -> Storage:
        return self._storage

    @storage.setter
    def storage(self, value):
        if self._storage is not None:
            logger.debug("Storage has already been set up")
            return

        elif not isinstance(value, Storage):
            logger.debug(f"Value must be of Storage type, but {type(value)} received")
            return

        else:
            self._storage = value
            return

    def error_file(self, path: StrPath) -> str:
        """
        The file name to provide in the error.

        Attributes
        ----------
        path : str or Path
            The path to the file.

        """
        return Path(relpath(path, self.base_dir())).as_posix()

    def inspect_anchor(self):
        """
        Setting the anchor from the link if any.

        """
        if not bool(self) or self.destination_file() is None:
            return

        if not isinstance(self.destination_file(), TextFile):
            logger.debug("Anchor cannot be in image")
            self._proper_anchor = ""

        elif self._link.anchor is None:
            logger.debug("Anchor is not set")
            self._proper_anchor = "/"

        elif self._link.anchor in self.destination_file().iter_anchors():
            logger.debug(f"Anchor {self._link.anchor} is ok")
            self._proper_anchor = f"/#{self._link.anchor}"

        else:
            self._proper_anchor = None

    def find_proper_anchor(self):
        """
        The attempt to find the valid anchor.

        """
        if self._proper_anchor is not None:
            return

        self._internal_inspector._text_file = self.destination_file()
        _proper_anchor: str | None = self._internal_inspector.modified_anchor(self._link.anchor)

        if _proper_anchor is not None:
            logger.warning(
                f"В файле {self.destination_file().rel_path} найден якорь\n"
                f"{_proper_anchor} вместо {self._link.anchor}", result=True)
            self._proper_anchor = _proper_anchor

        else:
            logger.error(
                f"Не найден якорь {self._link.anchor} в файле {self.error_file(self.destination_file().full_path)}\n"
                f"Ссылка {self._link.link_to} в файле {self.source_link().relative_to(self.base_dir())}")
            self._proper_anchor = "/#_valid_anchor_"

    def set_proper_link(self):
        """
        The preparation of the proper link.

        """
        if not bool(self):
            return

        if self._proper_link is not None:
            return

        _path: str = Path(relpath(self._destination, self.source_link())).as_posix()
        proper_link: str = _prepare_link(_path).removesuffix("/")

        if self._proper_anchor:
            proper_link: str = f"{_prepare_link(_path)}{self._proper_anchor}"

        if self._link.from_file.stem in ("index", "_index"):
            proper_link: str = proper_link.removeprefix("../")

        if not proper_link.startswith("."):
            proper_link: str = f"./{proper_link}"

        self._proper_link: str = proper_link

    def compare_links(self) -> bool:
        """
        The comparison of the original link and the proper one.

        Returns
        -------
        bool
            The result of the comparison.

        """
        if self._proper_link is None:
            logger.error(
                f"Файл {self.error_file(self._link.from_file)} по ссылке {self._link.link_to} не найден", result=True)
            return True

        elif self._proper_link == self._link.link_to:
            logger.debug("Links are equal")
            return True

        elif self._proper_anchor == "/#_valid_anchor_":
            logger.error(
                f"В файле {self.error_file(self._link.from_file)} ссылка должна быть:\n"
                f"{self._proper_link}, но получено\n{self._link.link_to}", result=True)
            return True

        else:
            logger.warning(
                f"В файле {self.error_file(self._link.from_file)} ссылка должна быть:\n"
                f"{self._proper_link}, но получено\n{self._link.link_to}", result=True)
            return False

    def clear(self):
        """
        Setting the values to None.

        """
        self._link: Link | None = None
        self._destination: Path | None = None
        self._proper_link: str | None = None
        self._proper_anchor: str | None = None

    @property
    def file_dict(self) -> FileDict:
        return self._file_dict

    @file_dict.setter
    def file_dict(self, value):
        if self._file_dict is not None:
            logger.debug("FileDict has already been set up")

        elif not isinstance(value, FileDict):
            logger.debug(f"Value must be of FileDict type, but {type(value)} received")

        else:
            self._file_dict = value

        return

    @property
    def link(self) -> Link:
        return self._link

    @link.setter
    def link(self, value):
        if value is None or isinstance(value, Link):
            self._link: Link | None = value

        else:
            logger.debug(f"Value must be of Link type or None, but {type(value)} received")

        return

    @property
    def proper_link(self) -> str | None:
        return self._proper_link

    def _names(self) -> tuple[str, ...]:
        """
        The possible names of the destination file in the storage.

        Returns
        -------
        tuple[str, ...]
            The names of the file having different number of parents.

        """
        _destination_name: str = self._link.stem
        _ext_destination_name: str = f"{self._link.parent_stem}/{self._link.stem}"
        _ext_ext_destination_name: str = f"{self._link.grandparent_stem}/{self._link.parent_stem}/{self._link.stem}"

        return _destination_name, _ext_destination_name, _ext_ext_destination_name


link_inspector: LinkInspector = LinkInspector()
link_inspector.__doc__ = "The default link inspector."
