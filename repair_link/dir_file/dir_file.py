# -*- coding: utf-8 -*-
from os.path import relpath
from pathlib import Path
from typing import Iterator, Iterable

from loguru import logger

from repair_link.dir_file.const import FileLinkItem, _InternalLink
from repair_link.general.const import StrPath, ADOC_EXTENSION, MD_EXTENSION, FilePattern, FileLanguage, Boundary
from repair_link.general.errors import LineInvalidTypeError, InternalLinkAnchorError


class DirFile:
    """
    The file in the directory.

    Attributes
    ----------
    _root_dir : str or Path
        The path to the directory.
    _full_path: str or Path
        The full path to the file.

    """

    def __init__(self, root_dir: StrPath, full_path: StrPath):
        self._root_dir: Path = Path(root_dir).resolve()
        self._full_path: Path = Path(full_path)

    def __bool__(self):
        return Path(self._full_path).suffix in (MD_EXTENSION, ADOC_EXTENSION)

    def __str__(self):
        return f"{self._full_path}"

    def __repr__(self):
        return f"<{self.__class__.__name__}({self._full_path})>"

    @property
    def rel_path(self) -> str:
        """
        The path to the file relative to the directory path.

        Returns
        -------
        str
            The relative path string.

        """
        return relpath(self._full_path, self._root_dir.parent.parent).replace("\\", "/")

    @property
    def full_path(self):
        return self._full_path


class TextFile(DirFile):
    _pattern_anchor: list[Boundary] = []

    def __init__(self, root_dir: StrPath, full_path: StrPath, patterns: FilePattern | None = None):
        super().__init__(root_dir, full_path)
        self._content: list[str] = []
        self._links: list[FileLinkItem] = []
        self._internal_links: set[_InternalLink] = set()
        self._anchors: set[str] = set()
        self._is_changed: bool = False
        self._patterns: FilePattern | None = patterns

    @classmethod
    def from_parent(cls, parent: DirFile):
        return cls(parent._root_dir, parent._full_path)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._content[item]
        else:
            raise LineInvalidTypeError(f"Тип должен быть int, но получен {type(item)}")

    def __setitem__(self, key, value):
        if isinstance(key, int) and isinstance(value, str):
            self._content[key] = value
        else:
            raise LineInvalidTypeError(
                f"Тип ключа должен быть int, а value - str, но получены {type(key)} и {type(value)}")

    def __contains__(self, item):
        if not isinstance(item, str):
            return False
        else:
            return item in self.iter_anchors()

    def __iter__(self):
        return iter(self._content)

    def read(self) -> bool:
        """
        Reading the file content.

        The method tries to open the text file and read each line.

        Handling UnicodeDecodeError, PermissionError, RuntimeError, FileNotFoundError, OSError.

        Returns
        -------
        bool
            The flag if the file contains text lines.

        """
        __flag: bool = False

        try:
            with open(self._full_path, "r+", encoding="utf-8") as f:
                self._content = f.readlines()

            __flag = True

        except UnicodeDecodeError as exc:
            logger.error(
                f"Ошибка декодирования символа, {exc.reason}\n"
                f"От {exc.start} до {exc.end}, в кодировке {exc.encoding}")

        except PermissionError:
            logger.error(f"Недостаточно прав для чтения файла {self.rel_path}")

        except RuntimeError:
            logger.error(f"Истекло время ожидания ответа во время чтения файла {self.rel_path}")

        except FileNotFoundError:
            logger.error(f"Файл {self.rel_path} был найден, но в течение работы скрипта был изменен")

        except OSError as exc:
            logger.error(
                f"Ошибка при работе с системой для файла {self.rel_path}, {exc.__class__.__name__}.\n"
                f"{exc.strerror}")

        finally:
            return __flag

    def write(self):
        """
        Writing the file content.

        The method tries to open the file and write all lines.

        Handling PermissionError, RuntimeError, FileNotFoundError, OSError.

        """
        _message: str = "В файл не внесены никакие изменения"

        if not self._is_changed:
            logger.debug(f"В файле {self.rel_path} нет изменений")
            return

        try:
            with open(self._full_path, "w+", encoding="utf-8") as f:
                f.write("".join(self._content))
            _message: str = f"Файл {self.rel_path} записан\n"

        except PermissionError:
            logger.error(f"Недостаточно прав для записи в файл {self.rel_path}")

        except RuntimeError:
            logger.error(f"Истекло время ожидания ответа во время записи файла {self.rel_path}")

        except FileNotFoundError:
            logger.error(f"Файл {self.rel_path} был найден, но в течение работы скрипта был изменен")

        except OSError as exc:
            logger.error(
                f"Ошибка при работе с системой для файла {self.rel_path}, {exc.__class__.__name__}.\n"
                f"{exc.strerror}")

        finally:
            logger.debug(_message)

    def iter_anchors(self) -> Iterator[str]:
        """
        Iteration of the anchors in the text file.

        Returns
        -------
        Iterator[str]
            The anchor iterator.

        """
        return iter(self._anchors)

    def iter_links(self) -> Iterator[FileLinkItem]:
        """Iterates of the links in the text file.

        :return: The link item iterator.
        :rtype: Iterator[FileLinkItem]
        """
        return iter(self._links)

    def _iter_internal_links(self) -> Iterator[_InternalLink]:
        """Iterates of the internal links in the text file.

        :return: The internal link item iterator.
        :rtype: Iterator[_InternalLink]
        """
        return iter(self._internal_links)

    def iter_internal_link_anchors(self) -> Iterator[str]:
        """Iterates the internal link anchors in the text file.

        :return: The internal link anchor iterator.
        :rtype: Iterator[str]
        """
        return iter(_.anchor for _ in self._iter_internal_links())

    def get_internal_links(self, anchor: str | None) -> tuple[_InternalLink, ...] | None:
        """Gets the internal links having the specified anchor.

        :param anchor: The anchor to find.
        :type anchor: str or None
        :return: The internal links.
        :rtype: tuple[_InternalLink] or None
        :raises: InternalLinkAnchorError if the anchor is found in neither internal link anchors.
        """
        if anchor is None:
            return

        if anchor not in self.iter_internal_link_anchors():
            raise InternalLinkAnchorError(f"В файле {self.rel_path} не обнаружен ни якорь, ни ссылка {anchor}")

        return tuple(filter(lambda x: x.anchor == anchor, self._iter_internal_links()))

    @property
    def is_changed(self):
        return self._is_changed

    @is_changed.setter
    def is_changed(self, value):
        if isinstance(value, bool):
            self._is_changed = value

    def update_line(self, line_number: int | Iterable[int], old_line: str, new_line: str, *, is_boundary: bool = False):
        """
        The modification of the line in the text file.

        Parameters
        ----------
        line_number : int | Iterable[int]
            The line index or indexes in the text file.
        old_line : str
            The current line in the text file.
        new_line : str
            The text to replace in the text file.
        is_boundary : bool
            The flag to use boundaries for anchors.
        """
        if not self._is_changed:
            self._is_changed = True

        if not is_boundary:
            boundaries: list[Boundary] | None = None
        else:
            boundaries: list[Boundary] | None = self._pattern_anchor

        def single_number(_index: int, _boundaries: list[Boundary] = None):
            if _boundaries is None:
                _boundaries: list[Boundary] = [Boundary()]

            for boundary in _boundaries:
                self[_index] = self[_index].replace(boundary.bound(old_line), boundary.bound(new_line))

        if isinstance(line_number, int):
            single_number(line_number, boundaries)

        else:
            for index in line_number:
                single_number(index, boundaries)

        logger.success(f"{old_line} -> {new_line}, в файле {self.rel_path} в строках: {line_number}\n")

    def find_anchor(self, anchor: str) -> list[int]:
        return [
            index for index, line in enumerate(iter(self))
            if any(boundary.bound(anchor) in line for boundary in self._pattern_anchor)]

    @property
    def language(self) -> FileLanguage:
        """Specifies the file language."""
        if ".en" in self.full_path.suffixes or self.full_path.stem.endswith("_en"):
            return FileLanguage.EN

        else:
            return FileLanguage.RU

    def set_links(self):
        """Specifies the links in the text file."""
        raise NotImplementedError

    def set_internal_links(self):
        """Specifies the internal links in the text file."""
        raise NotImplementedError

    def set_anchors(self):
        """Specifies the anchors in the text file."""
        raise NotImplementedError

    def set_imagesdir(self):
        """Specifies the 'imagesdir' value if given."""
        pass
