# -*- coding: utf-8 -*-
from typing import NamedTuple

from repair_link.general.link import Link


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
    """
    The instance to bind the link with the file.

    Attributes
    ----------
    index : int
        The index of the line in the file.
    link : Link
        The link from the file.

    """
    index: int
    link: Link

    def __str__(self):
        return f"{self.__class__.__name__}:\nline number {self.index}\nlink {self.link}"

    def __repr__(self):
        return f"<{self.__class__.__name__}({self._asdict()})>"
