# -*- coding: utf-8 -*-
from re import sub, Match
from typing import Iterator

from loguru import logger

from utilities.common.errors import FileInvalidTypeError, InvalidMatchError
from utilities.link_repair.file_dict import TextFile

__all__ = ["InternalLinkInspector", "internal_inspector"]


def _replace_dash_underline(match: Match) -> str:
    """Replaces snake_case and kebab-case with camelCase.

    :param match: The substring matching the pattern.
    :type match: Match
    :return: The updated string converted to camelCase.
    :rtype: str
    :raises: InvalidMatchError if the line does not have dashes or underlines in proper places.
    """
    if not match:
        logger.error(f"В строке не найден паттерн {match.re.pattern}")
        raise InvalidMatchError

    else:
        return str(match.group(2).upper())


def _iter_internal_options(line: str) -> Iterator[str]:
    """Iterates over updated forms of line.

    The updated forms are snake_case, kebab-case, and camelCase.

    :param line: The line to switch the case.
    :type line: str
    :return: The new form of line converted to one of the cases.
    :rtype: Iterator[str]
    """
    to_underline: str = line.replace("-", "_")
    to_dash: str = line.replace("_", "-")
    to_camel_case: str = sub("([-_])(\\w)", _replace_dash_underline, line)

    return iter((to_underline, to_dash, to_camel_case))


class InternalLinkInspector:
    """
    Class to represent the inspector for internal links having only anchors.

    :param _text_file: The markdown file to inspect internal links.
    :type _text_file : TextFile or None
    """

    def __init__(self):
        self._text_file: TextFile | None = None

    def __str__(self):
        return f"{self.__class__.__name__}()"

    def __repr__(self):
        return f"<{self.__class__.__name__}()>"

    @property
    def text_file(self) -> TextFile:
        return self._text_file

    @text_file.setter
    def text_file(self, value):
        if isinstance(value, TextFile):
            self._text_file = value

        else:
            logger.error(f"Файл должен быть типа TextFile, но получено {type(value)}")
            raise FileInvalidTypeError

    def modified_anchor(self, anchor: str) -> str | None:
        """Gets the possible modified original anchor.

        :param anchor: The original anchor from the link.
        :type anchor: str
        :return: The modified anchor found in the file.
        :rtype: str
        """
        for _modified_anchor in _iter_internal_options(anchor):
            if _modified_anchor in self._text_file.iter_anchors():
                return _modified_anchor

        else:
            return

    @property
    def _dir_file_anchors(self) -> set[str]:
        """Gets anchors in the file.

        :return: The found anchors in the file as is.
        :rtype: set[str]
        """
        return set(self._text_file.iter_anchors())

    def _missing_anchors(self) -> set[str]:
        """Gets the anchors not found in the file.

        :return: The bad internal links in the file.
        :rtype: set[str]
        """
        _link_anchors: set[str] = set(self._text_file.iter_internal_link_anchors())

        return _link_anchors.difference(self._dir_file_anchors)

    def inspect_links(self):
        """Validates and updates the internal links."""
        if not self._missing_anchors():
            logger.debug("All internal links and anchors are valid")
            return

        for _anchor in self._missing_anchors():
            _modified_anchor: str | None = self.modified_anchor(_anchor)

            if _modified_anchor is not None:
                logger.warning(
                    f"В файле {self._text_file.rel_path} найден якорь\n"
                    f"{_modified_anchor} вместо {_anchor}", result=True)

                for _i_link in self._text_file.get_internal_links(_anchor):
                    self._text_file.update_line(_i_link.index, _i_link.anchor, _modified_anchor)

                logger.success(
                    f"Файл {self._text_file.rel_path}:\n"
                    f"{_anchor} -> {_modified_anchor}\n", result=True)

            else:
                _indexes: str = ", ".join(
                    str(_internal_link.index) for _internal_link in self._text_file.get_internal_links(_anchor))
                logger.error(
                    f"Не найден якорь {_anchor} в файле {self._text_file.rel_path}.\n"
                    f"Строки: {_indexes}", result=True)


internal_inspector: InternalLinkInspector = InternalLinkInspector()
internal_inspector.__doc__ = "The default internal link inspector."
