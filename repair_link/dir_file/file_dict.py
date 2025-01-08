# -*- coding: utf-8 -*-
from os.path import relpath
from pathlib import Path
from typing import Iterable, Iterator

from loguru import logger

from repair_link.dir_file.dir_file import TextFile, DirFile
from repair_link.general.const import StrPath, ADOC_EXTENSION, MD_EXTENSION
from repair_link.dir_file.text_file import AsciiDocFile, MdFile


def get_file(root_dir: StrPath, full_path: StrPath) -> MdFile | AsciiDocFile:
    """
    Specifying the type of the file.

    Attributes
    ----------
    root_dir : str or Path
        The path to the directory.
    full_path : str or Path
        The absolute path to the file.

    Returns
    -------
    MdFile or AsciiDocFile
        The specified file according to the extension.

    """
    if full_path.suffix == MD_EXTENSION:
        return MdFile(root_dir, full_path)

    elif full_path.suffix == ADOC_EXTENSION:
        return AsciiDocFile(root_dir, full_path)


class FileDict:
    """
    The dictionary of the files inside the directory.

    Attributes
    ----------
    _root_dir : StrPath
        The directory path.
    _dict_files : dict[Path, TextFile]
        The dictionary of the paths and the files.

    """

    def __init__(self, root_dir: StrPath):
        self._root_dir: Path = Path(root_dir).resolve()
        self._dict_files: dict[Path, DirFile] = dict()

    def __repr__(self):
        _paths: str = "\n".join([f"{_path}" for _path in self._dict_files])
        return f"{self.__class__.__name__}, dict_files:\n{_paths}"

    __str__ = __repr__

    @property
    def dict_files(self):
        return self._dict_files

    @dict_files.setter
    def dict_files(self, value):
        self._dict_files = value

    def __contains__(self, item):
        if not isinstance(item, (str, Path)):
            return False
        else:
            return Path(item) in self._dict_files

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return True
        else:
            return False

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return False
        else:
            return True

    def __add__(self, other):
        def _add_file(__path: StrPath):
            file_path: Path = Path(__path).resolve()

            if file_path in self:
                logger.debug(f"Path {file_path} is already listed")
                return

            if file_path.suffix in (MD_EXTENSION, ADOC_EXTENSION):
                text_file: TextFile = get_file(self._root_dir, file_path)

                if text_file.read():
                    text_file.set_imagesdir()
                    text_file.set_links()
                    text_file.set_anchors()
                    text_file.set_internal_links()

                self[file_path] = text_file

            else:
                self[file_path] = DirFile(self._root_dir, file_path)

        if isinstance(other, (str, Path)):
            _add_file(other)

        elif isinstance(other, Iterable):
            for item in filter(lambda x: isinstance(x, (str, Path)), other):
                _add_file(item)

        else:
            logger.debug(f"Элемент {other} должен быть типа str или Path, но получено {type(other)}")
        return

    __radd__ = __add__
    __iadd__ = __add__

    def __iter__(self) -> Iterator[DirFile]:
        return iter(filter(lambda x: isinstance(x, TextFile), self._dict_files.values()))

    def __getitem__(self, item):
        if not isinstance(item, (str, Path)):
            logger.exception(f"Элемент {item} должен быть типа str или Path, но получено {type(item)}", result=True)
            return

        if item not in self:
            _relpath: str = relpath(item, self._root_dir.parent.parent).replace("\\", "/")
            return

        return self._dict_files.get(Path(item))

    get = __getitem__

    def __setitem__(self, key, value):
        if isinstance(key, (str, Path)) and isinstance(value, DirFile):
            self._dict_files[key] = value
        else:
            logger.debug(
                f"Ключ {key} должен быть типа str или Path, а значение {value} типа TextFile, "
                f"но получены {type(key)} и {type(value)}")
