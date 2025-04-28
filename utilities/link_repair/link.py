# -*- coding: utf-8 -*-
from enum import Enum
from pathlib import Path
from typing import NamedTuple

from utilities.common.shared import ADOC_EXTENSION, EXTENSIONS, MD_EXTENSION, StrPath


class _LinkType(Enum):
    """Class to represent the type of the link."""
    IMAGE_TYPE = "image"
    TEXT_TYPE = "text"
    DIR_INDEX_TYPE = "dir_index"
    DIRINDEX_TYPE = "dirindex"

    def __str__(self):
        return f"{self.__class__.__name__}: {self._name_}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>({self._value_})"


class Link(NamedTuple):
    # noinspection PyUnresolvedReferences
    """Class to represent the link from the file leading to the other file in the same directory.

    :param from_file: The path to the file containing the link.
    :type from_file: str or Path
    :param link_to: The text of the link given in curly brackets.
    :type link_to: str
    """
    from_file: StrPath
    link_to: str

    def __str__(self):
        return f"{self.__class__.__name__}: link {self.link_to} from {self.from_file}"

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.from_file} -> {self.link_to})>"

    def __bool__(self):
        return "#" in self.link_to

    def origin_destination_path(self) -> Path:
        """Gets the origin path to the destination file from the link."""
        if self.from_type in (_LinkType.DIRINDEX_TYPE, _LinkType.DIR_INDEX_TYPE):
            _real_link_to_file: str = f"../{self.link_to_file}"

        else:
            _real_link_to_file: str = self.link_to_file

        return self.from_file.joinpath(_real_link_to_file).resolve()

    @property
    def anchor(self) -> str | None:
        """Gets the anchor from the link if any."""
        if bool(self):
            return self.link_to.rsplit("#", 1)[-1].removesuffix("/")

        else:
            return None

    @property
    def stem(self) -> str:
        """Gets the origin stem of the path to the destination file from the link."""
        return (self
                .origin_destination_path()
                .name
                .removesuffix(MD_EXTENSION)
                .removesuffix(ADOC_EXTENSION))

    @property
    def parent_stem(self) -> str:
        """Gets the stem of the destination file parent from the link."""
        return self.origin_destination_path().parent.name

    @property
    def grandparent_stem(self) -> str:
        """Gets the stem of the destination file grandparent from the link."""
        return self.origin_destination_path().parent.parent.name

    @property
    def from_type(self) -> _LinkType:
        """Gets the category of the link.

        :return: The type of the link based on the extension and index/_index files.
        :rtype: _LinkType
        """
        if self.from_file.suffix not in EXTENSIONS:
            return _LinkType.IMAGE_TYPE

        elif self.from_file.stem.startswith("index"):
            return _LinkType.DIR_INDEX_TYPE

        elif self.from_file.stem.startswith("_index"):
            return _LinkType.DIRINDEX_TYPE

        else:
            return _LinkType.TEXT_TYPE

    @property
    def link_to_file(self) -> str:
        """Gets the link to the file with no anchor."""
        if bool(self):
            return self.link_to.rsplit("#", 1)[0].removesuffix("/")

        else:
            return self.link_to.removesuffix("/")

    @property
    def is_component(self) -> bool:
        """Gets the flag of the original file to be in the 'components' directory."""
        return "components" in self.from_file.parts

    @property
    def component_name(self) -> str | None:
        """Gets the name of the component the file is located in.

        :return: The component name if any, otherwise, None.
        :rtype: str or None
        """
        if self.is_component:
            _: tuple[str, ...] = self.from_file.parts

            for index, part in enumerate(self.from_file.parts):
                if part == "components":
                    return _[index + 1]

        else:
            return None
