# -*- coding: utf-8 -*-
from pathlib import Path
from re import compile, findall, finditer, Match, Pattern, search
from typing import Iterable, Iterator, NamedTuple

from loguru import logger

from utilities.common.errors import LinkRepairInternalLinkAnchorError, LinkRepairLineInvalidTypeError
from utilities.common.functions import file_reader
from utilities.common.shared import ADOC_EXTENSION, MD_EXTENSION, StrPath
from utilities.link_repair.const import FileLanguage, prepare_logging
from utilities.link_repair.link import Link


class FilePattern(NamedTuple):
    """Class to represent the patterns to get link parts of specified types.

    :param pattern_anchor: The pattern to get the link anchor.
    :type pattern_anchor: str
    :param pattern_link: The pattern to get the link.
    :type pattern_link: str
    :param pattern_internal_link: The pattern to get the internal link.
    :type pattern_internal_link: str
    """
    pattern_anchor: str
    pattern_link: str
    pattern_internal_link: str

    def __str__(self):
        return (
            f"ANCHOR: {self.pattern_anchor}\n"
            f"LINK: {self.pattern_link}\n"
            f"INTERNAL_LINK: {self.pattern_internal_link}")

    __repr__ = __str__


class Boundary(NamedTuple):
    """Class to represent the prefix and the suffix.

    :param before: The prefix.
    :type before: str
    :param after: The suffix.
    :type after: str
    """
    before: str = ""
    after: str = ""

    def bound(self, value: str):
        return f"{self.before}{value}{self.after}"


class _InternalLink(NamedTuple):
    """Class to represent the link to the anchor in the same file.

    :param index: The index of the line in the file.
    :type index: int
    :param anchor: The anchor in the link.
    :type anchor: str
    """
    index: int
    anchor: str

    def __str__(self):
        return f"{self.__class__.__name__}:\nline number {self.index}\nlink {self.anchor}"

    def __repr__(self):
        return f"<{self.__class__.__name__}({self._asdict()})>"


class FileLinkItem(NamedTuple):
    """Class to represent the instance to bind the link with the file.

    :param index: The index of the line in the file.
    :type index: int
    :param link: The link from the file.
    :type link: Link
    """
    index: int
    link: Link

    def __str__(self):
        return f"{self.__class__.__name__}:\nline number {self.index}\nlink {self.link}"

    def __repr__(self):
        return f"<{self.__class__.__name__}({self._asdict()})>"


# noinspection PyUnresolvedReferences
class DirFile:
    """Class to represent the file in the directory.

    :param _root_dir: The path to the directory.
    :type _root_dir: str or Path
    :param _full_path: The full path to the file.
    :type _full_path: str or Path
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
        """Specifies the path to the file relative to the directory path."""
        return self._full_path.relative_to(self._root_dir.parent.parent).as_posix()

    @property
    def full_path(self):
        return self._full_path


# noinspection PyUnresolvedReferences
class TextFile(DirFile):
    """Class to represent the text file in the directory.

    :param _content: The lines of the file.
    :type _content: list[str]
    :param _links: The links instances.
    :type _links: list[FileLinkItem]
    :param _internal_links: The internal links.
    :type _internal_links: set[_InternalLink]
    :param _anchors: The link anchors.
    :type _anchors: set[str]
    :param _is_changed: The flag if the file has been modified.
    :type _is_changed: bool
    :param _patterns: The patterns that used for the file.
    :type _patterns: FilePattern or None
    """
    _pattern_anchor: list[Boundary] = []
    IGNORED_LINKS: tuple[str, ...] = ("http", "mailto", "/", "#")

    def __init__(self, root_dir: StrPath, full_path: StrPath, patterns: FilePattern | None = None):
        super().__init__(root_dir, full_path)
        self._content: list[str] = []
        self._links: list[FileLinkItem] = []
        self._internal_links: set[_InternalLink] = set()
        self._anchors: set[str] = set()
        self._is_changed: bool = False
        self._patterns: FilePattern | None = patterns

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._content[item]

        else:
            raise LinkRepairLineInvalidTypeError(f"Тип должен быть int, но получен {type(item)}")

    def __setitem__(self, key, value):
        if isinstance(key, int) and isinstance(value, str):
            self._content[key] = value

        else:
            raise LinkRepairLineInvalidTypeError(
                f"Тип ключа должен быть int, а value - str, но получены {type(key)} и {type(value)}")

    def __contains__(self, item):
        if not isinstance(item, str):
            return False

        else:
            return item in self.iter_anchors()

    def __iter__(self):
        return iter(self._content)

    def iter_anchors(self) -> Iterator[str]:
        """Iterates the anchors in the text file.

        :return: The anchor iterator.
        :rtype: Iterator[str]
        """
        return iter(self._anchors)

    def iter_links(self) -> Iterator[FileLinkItem]:
        """Iterates the links in the text file.

        :return: The link item iterator.
        :rtype: Iterator[FileLinkItem]
        """
        return iter(self._links)

    def _iter_internal_links(self) -> Iterator[_InternalLink]:
        """Iterates the internal links in the text file.

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
        :raises: LinkRepairInternalLinkAnchorError if the anchor is found in neither internal link anchors.
        """
        if anchor is None:
            return

        elif anchor not in self.iter_internal_link_anchors():
            logger.error(f"В файле {self.rel_path} не обнаружен ни якорь, ни ссылка {anchor}")
            raise LinkRepairInternalLinkAnchorError

        else:
            return tuple(filter(lambda x: x.anchor == anchor, self._iter_internal_links()))

    @property
    def is_changed(self):
        return self._is_changed

    @is_changed.setter
    def is_changed(self, value):
        if isinstance(value, bool):
            self._is_changed = value

    def update_line(
            self,
            line_number: int | Iterable[int],
            old_line: str,
            new_line: str, *,
            is_boundary: bool = False):
        """Modifies the line in the text file.

        :param line_number: The line index or indexes in the text file.
        :type line_number: int | Iterable[int]
        :param old_line: The current line in the text file.
        :type old_line: str
        :param new_line: The text to replace in the text file.
        :type new_line: str
        :param is_boundary: The flag to use boundaries for anchors.
        :type is_boundary: bool
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

        logger.success(f"{old_line} -> {new_line}, в файле {self.rel_path} в строках: {line_number}")

    def find_anchor(self, anchor: str) -> list[int]:
        """Searches for the indexes of the anchor.

        :param anchor: The specified anchor.
        :type anchor: str
        :return: The indexes.
        :rtype: list[int]
        """
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

    @property
    def content(self):
        return self._content


# noinspection PyUnresolvedReferences
class MdFile(TextFile):
    """Class to represent the Markdown file in the directory.

    :param _root_dir: The path to the directory.
    :type _root_dir: str or Path
    :param _content: The lines inside the file.
    :type _content: list[str]
    :param _links: The links inside the file.
    :type _links: list[FileLinkItem]
    :param _internal_links: The internal links inside the file.
    :type _internal_links: set[_InternalLink]
    :param _anchors: The anchors inside the file.
    :type _anchors: list[str]
    :param _is_changed: The flag of changes in the file.
    :type _is_changed: bool
    """
    _pattern_anchor: list[Boundary] = [
        Boundary("{#", "}"),
        Boundary("<a name=\"", "\">"),
        Boundary("#")]

    def __init__(self, root_dir: StrPath, full_path: StrPath):
        _MD_ANCHOR_HEADING: str = r"(?<=\{#)[\w_-]+(?=})"
        _MD_ANCHOR_A_NAME: str = r"(?<=<a\sname=\")[^\"]+(?=\">)"
        _MD_ANCHOR_A_ID: str = r"(?<=<a\sid=\")[^\"]+(?=\">)"

        md_file_pattern: FilePattern = FilePattern(
            rf"{_MD_ANCHOR_HEADING}|{_MD_ANCHOR_A_NAME}|{_MD_ANCHOR_A_ID}",
            r"\[[^]]+]\(([^)]+)\)",
            r"\[[^]]+]\(#([^)]+)\)")

        super().__init__(root_dir, full_path, md_file_pattern)

    def set_anchors(self):
        """Specifies the anchors in the Markdown file."""
        for line in iter(self):
            _m: list[str] = findall(self._patterns.pattern_anchor, line.removesuffix("\n"))

            if _m:
                self._anchors.update(_m)

        logger.debug(f"File {self.rel_path}, anchors:\n{prepare_logging(self._anchors)}")

    def set_links(self):
        """Specifies the links in the Markdown file."""
        for index, line in enumerate(iter(self)):
            for _m in finditer(self._patterns.pattern_link, line.removesuffix("\n")):
                _link_to: str = _m.group(1)

                if _link_to.startswith(self.__class__.IGNORED_LINKS):
                    logger.debug(f"Link {_link_to} leads to the external source")
                    continue

                else:
                    _: FileLinkItem = FileLinkItem(index, Link(self._full_path, _link_to))
                    self._links.append(_)

        logger.debug(
            f"File {self.rel_path}, "
            f"links:\n{prepare_logging(_.link.link_to for _ in self.iter_links())}")

    def set_internal_links(self):
        """Specifies the internal links in the Markdown file."""
        for index, line in enumerate(iter(self)):
            for _m in finditer(self._patterns.pattern_internal_link, line.removesuffix("\n")):
                _anchor: str = _m.group(1)
                _: _InternalLink = _InternalLink(index, _anchor)
                self._internal_links.add(_)

        logger.debug(
            f"File {self.rel_path}, "
            f"internal links:\n{prepare_logging(_.anchor for _ in self._iter_internal_links())}")


# noinspection PyUnresolvedReferences
class AsciiDocFile(TextFile):
    """Class to represent the AsciiDoc file in the directory.

    :param _root_dir: The path to the directory.
    :type _root_dir: str or Path
    :param _content: The lines inside the file.
    :type _content: list[str]
    :param _links: The links inside the file.
    :type _links: list[FileLinkItem]
    :param _internal_links: The internal links inside the file.
    :type _internal_links: set[_InternalLink]
    :param _anchors: The anchors inside the file.
    :type _anchors: list[str]
    :param _is_changed: The flag of changes in the file.
    :type _is_changed: bool
    """
    _pattern_anchor: list[Boundary] = [
        Boundary("[#", "]"),
        Boundary("[[", "]]"),
        Boundary("#"),
        Boundary("<<", ",")]

    def __init__(self, root_dir: StrPath, full_path: StrPath):
        ascii_doc_file_pattern: FilePattern = FilePattern(
            r"(?<=\[[\[#])[^]]+(?=])",
            r"(?<=xref:)[^\[]+(?=\[)|(?<=link:)[^\[]+(?=\[)|(?<=image::)[^\[]+(?=\[)|(?<=image:)[^\[]+(?=\[)",
            r"(?<=<<)([^,>]+)[^>]*(?=>>)")

        super().__init__(root_dir, full_path, ascii_doc_file_pattern)
        self._imagesdir: str | None = "./"

    def set_imagesdir(self):
        """Specifies the 'imagesdir' value if given."""
        for line in iter(self):
            if ":imagesdir:" not in line:
                continue

            else:
                _pattern: Pattern = compile(r"(?<=:imagesdir:)[^]]+")
                _m: Match = search(_pattern, line)
                self._imagesdir = f"{_m.string[_m.start():_m.end()]}".strip().removesuffix("/")
                break

    def set_anchors(self):
        """Specifies the anchors in the AsciiDoc file."""
        for line in iter(self):
            _m: list[str] = findall(self._patterns.pattern_anchor, line.removesuffix("\n"))

            if _m:
                self._anchors.update(_m)

        logger.debug(
            f"File {self.rel_path}, anchors:\n{prepare_logging(self._anchors)}")

    def set_links(self):
        """Specifies the links in the AsciiDoc file."""
        for index, line in enumerate(iter(self)):
            for _m in finditer(self._patterns.pattern_link, line.removesuffix("\n")):
                if "image" in f"{_m.string}":
                    _base_link_to: str = f"{_m.string[_m.start():_m.end()]}".removeprefix(":")
                    _link_to: str = f"{self._imagesdir}/{_base_link_to}"

                else:
                    _link_to: str = f"{_m.string[_m.start():_m.end()]}"

                if _link_to.startswith(self.__class__.IGNORED_LINKS):
                    logger.debug(f"Link {_m} leads to the external source")
                    continue

                else:
                    _: FileLinkItem = FileLinkItem(index, Link(self._full_path, _link_to))
                    self._links.append(_)

        logger.debug(
            f"File {self.rel_path}, "
            f"links:\n{prepare_logging(_.link.link_to for _ in self.iter_links())}")

    def set_internal_links(self):
        """Specifies the internal links in the AsciiDoc file."""
        for index, line in enumerate(iter(self)):
            for _m in finditer(self._patterns.pattern_internal_link, line.removesuffix("\n")):
                _anchor: str = _m.group(1)
                _: _InternalLink = _InternalLink(index, _anchor)
                self._internal_links.add(_)

        logger.debug(
            f"File {self.rel_path}, "
            f"internal links:\n{prepare_logging(_.anchor for _ in self._iter_internal_links())}")


def get_file(root_dir: StrPath, full_path: StrPath) -> MdFile | AsciiDocFile:
    """Specifies the type of the file.

    :param root_dir: The path to the directory.
    :type root_dir: str or Path
    :param full_path: The absolute path to the file.
    :type full_path: str or Path
    :return: The specified file according to the extension.
    :rtype: MdFile or AsciiDocFile
    """
    if full_path.suffix == MD_EXTENSION:
        return MdFile(root_dir, full_path)

    elif full_path.suffix == ADOC_EXTENSION:
        return AsciiDocFile(root_dir, full_path)


# noinspection PyUnresolvedReferences
class FileDict:
    """Class to represent the dictionary of the files inside the directory.

    :param _root_dir: The directory path.
    :type _root_dir: StrPath
    :param _dict_files: The dictionary of the paths and the files.
    :type _dict_files: dict[Path, TextFile]
    """

    def __init__(self, root_dir: StrPath):
        self._root_dir: Path = Path(root_dir).resolve()
        self._dict_files: dict[Path, DirFile] = {}

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

                text_file._content = file_reader(text_file.full_path, "lines", encoding="utf-8")
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

    __radd__ = __add__
    __iadd__ = __add__

    def __iter__(self) -> Iterator[DirFile]:
        return iter(filter(lambda x: isinstance(x, TextFile), self._dict_files.values()))

    def __getitem__(self, item):
        if not isinstance(item, (str, Path)):
            logger.exception(f"Элемент {item} должен быть типа str или Path, но получено {type(item)}", result=True)
            return

        else:
            return self._dict_files.get(Path(item))

    def get(self, item):
        return self.__getitem__(item)

    def __setitem__(self, key, value):
        if isinstance(key, (str, Path)) and isinstance(value, DirFile):
            self._dict_files[key] = value

        else:
            logger.debug(
                f"Ключ {key} должен быть типа str или Path, а значение {value} типа TextFile, "
                f"но получены {type(key)} и {type(value)}")
