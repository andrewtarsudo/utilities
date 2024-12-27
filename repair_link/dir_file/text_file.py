# -*- coding: utf-8 -*-
from re import findall, finditer, Pattern, search, Match, compile

from loguru import logger

from repair_link.dir_file.dir_file import TextFile, FileLinkItem, _InternalLink
from repair_link.general.const import StrPath, md_file_pattern, IGNORED_LINKS, ascii_doc_file_pattern, ADOC_EXTENSION, \
    MD_EXTENSION, prepare_logging, Boundary
from repair_link.general.link import Link


class MdFile(TextFile):
    """
    The markdown file in the directory.

    Attributes
    ----------
    _root_dir : str or Path
        The path to the directory.
    _content : list[str]
        The lines inside the file.
    _links : list[FileLinkItem]
        The links inside the file.
    _internal_links : set[_InternalLink]
        The internal links inside the file.
    _anchors : list[str]
        The anchors inside the file.
    _is_changed : bool
        The flag of changes in the file.

    """
    _pattern_anchor: list[Boundary] = [Boundary("{#", "}"), Boundary("<a name=\"", "\">"), Boundary("#")]

    def __init__(self, root_dir: StrPath, full_path: StrPath):
        super().__init__(root_dir, full_path, md_file_pattern)

    def set_anchors(self):
        """
        Specifying the anchors in the Markdown file.

        """
        for line in iter(self):
            _m: list[str] = findall(self._patterns.pattern_anchor, line.removesuffix("\n"))
            if _m:
                self._anchors.update(_m)

        logger.debug(f"File {self.rel_path}, anchors:\n{prepare_logging(self._anchors)}")
        return

    def set_links(self):
        """
        Specifying the links in the Markdown file.

        """
        for index, line in enumerate(iter(self)):
            for _m in finditer(self._patterns.pattern_link, line.removesuffix("\n")):
                _link_to: str = _m.group(1)

                if _link_to.startswith(IGNORED_LINKS):
                    logger.debug(f"Link {_link_to} leads to the external source")
                    continue

                else:
                    _: FileLinkItem = FileLinkItem(index, Link(self._full_path, _link_to))
                    self._links.append(_)

        logger.debug(
            f"File {self.rel_path}, "
            f"links:\n{prepare_logging(_.link.link_to for _ in self.iter_links())}")
        return

    def set_internal_links(self):
        """
        Specifying the internal links in the Markdown file.

        """
        for index, line in enumerate(iter(self)):
            for _m in finditer(self._patterns.pattern_internal_link, line.removesuffix("\n")):
                _anchor: str = _m.group(1)
                _: _InternalLink = _InternalLink(index, _anchor)
                self._internal_links.add(_)

        logger.debug(
            f"File {self.rel_path}, "
            f"internal links:\n{prepare_logging(_.anchor for _ in self._iter_internal_links())}")
        return


class AsciiDocFile(TextFile):
    """
    The AsciiDoc file in the directory.

    Attributes
    ----------
    _root_dir : str or Path
        The path to the directory.
    _content : list[str]
        The lines inside the file.
    _links : list[FileLinkItem]
        The links inside the file.
    _internal_links : set[_InternalLink]
        The internal links inside the file.
    _anchors : list[str]
        The anchors inside the file.
    _is_changed : bool
        The flag of changes in the file.

    """
    _pattern_anchor: list[Boundary] = [Boundary("[#", "]"), Boundary("[[", "]]"), Boundary("#"), Boundary("<<", ",")]

    def __init__(self, root_dir: StrPath, full_path: StrPath):
        super().__init__(root_dir, full_path, ascii_doc_file_pattern)
        self._imagesdir: str | None = "./"

    def set_imagesdir(self):
        """
        Specifying the 'imagesdir' value if given.

        """
        for line in iter(self):
            if ":imagesdir:" not in line:
                continue

            else:
                _pattern: Pattern = compile(r"(?<=:imagesdir:)[^]]+")
                _m: Match = search(_pattern, line)
                self._imagesdir = f"{_m.string[_m.start():_m.end()]}".strip().removesuffix("/")
                break

    def set_anchors(self):
        """
        Specifying the anchors in the AsciiDoc file.

        """
        for line in iter(self):
            _m: list[str] = findall(self._patterns.pattern_anchor, line.removesuffix("\n"))
            if _m:
                self._anchors.update(_m)

        logger.debug(
            f"File {self.rel_path}, anchors:\n{prepare_logging(self._anchors)}")
        return

    def set_links(self):
        """
        Specifying the links in the AsciiDoc file.

        """
        for index, line in enumerate(iter(self)):
            for _m in finditer(self._patterns.pattern_link, line.removesuffix("\n")):
                if "image" in f"{_m.string}":
                    _base_link_to: str = f"{_m.string[_m.start():_m.end()]}".removeprefix(":")
                    _link_to: str = f"{self._imagesdir}/{_base_link_to}"

                else:
                    _link_to: str = f"{_m.string[_m.start():_m.end()]}"

                if _link_to.startswith(IGNORED_LINKS):
                    logger.debug(f"Link {_m} leads to the external source")
                    continue

                else:
                    _: FileLinkItem = FileLinkItem(index, Link(self._full_path, _link_to))
                    self._links.append(_)

        logger.debug(
            f"File {self.rel_path}, "
            f"links:\n{prepare_logging(_.link.link_to for _ in self.iter_links())}")
        return

    def set_internal_links(self):
        """
        Specifying the internal links in the AsciiDoc file.

        """
        for index, line in enumerate(iter(self)):
            for _m in finditer(self._patterns.pattern_internal_link, line.removesuffix("\n")):
                _anchor: str = _m.group(1)
                _: _InternalLink = _InternalLink(index, _anchor)
                self._internal_links.add(_)

        logger.debug(
            f"File {self.rel_path}, "
            f"internal links:\n{prepare_logging(_.anchor for _ in self._iter_internal_links())}")
        return


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
