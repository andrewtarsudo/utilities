# -*- coding: utf-8 -*-
from re import finditer, Match, sub

from loguru import logger

from repair_link.dir_file.dir_file import TextFile
from repair_link.general.const import PATTERN
from repair_link.general.errors import FixerNoLinkError, InvalidHashCharIndexError


class LinkFixer:
    """
    The instance to fix links.

    Attributes
    ----------
    _text_file : TextFile or None
        The file in the directory.

    """

    def __init__(self):
        self._text_file: TextFile | None = None

    def __repr__(self):
        return f"{self.__class__.__name__}"

    __str__ = __repr__

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return True
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return False
        else:
            return NotImplemented

    def __iter__(self):
        return self._text_file.iter_links()

    def __bool__(self):
        return self._text_file is not None

    @property
    def text_file(self):
        return self._text_file

    @text_file.setter
    def text_file(self, value):
        self._text_file = value

    def _validate(self):
        """
        Inspecting if the file is specified.

        """
        if not bool(self):
            logger.error("Не задан файл")
            raise FixerNoLinkError

    def _fix_whitespaces(self):
        """
        Fixing errors when the link has whitespaces.

        """
        for link in iter(self):
            _: str = link.link.link_to

            if " " in _:
                self._text_file.update_line(link.index, _, _.replace(" ", ""))
                logger.warning(
                    f"В файле {self._text_file.rel_path} некорректная ссылка:\n"
                    f"{_}\n"
                    f"Строка: {link.index}", result=True)

        if self._text_file.is_changed is False:
            logger.debug(f"file {self._text_file.rel_path}, no whitespaces to fix")

    def _fix_missing_slashes_after_dots(self):
        """
        Fixing errors when the link has double dots with no slash followed.

        """

        def add_slash(match: Match):
            return f"{match.group(1)}/{match.group(2)}"

        for link in iter(self):
            _: str = link.link.link_to

            for _m in finditer(PATTERN, _):
                if _m:
                    self._text_file.update_line(link.index, _, sub(PATTERN, add_slash, _))
                    self._text_file.is_changed = True
                    logger.warning(
                        f"В файле {self._text_file.rel_path} некорректная ссылка:\n"
                        f"{_}\n"
                        f"Строка: {link.index}", result=True)

        if self._text_file.is_changed is False:
            logger.debug(f"file {self._text_file.rel_path}, no missing slashes to fix")

    def _fix_missing_slashes_before_hash(self):
        """
        Fixing errors when the link has an anchor with no slash before.

        """
        for link in iter(self):
            _: str = link.link.link_to

            if bool(link.link):
                index: int = _.find("#") - 1

                if index < -1:
                    logger.error(
                        f"Позиция # в файле {self._text_file.rel_path} в ссылке {_} определена как {index}, "
                        f"что некорректно")
                    raise InvalidHashCharIndexError

                elif index == -1:
                    logger.debug(f"Link {link} is internal")
                    continue

                elif _[index] != "/":
                    self._text_file.update_line(link.index, _, _.replace("#", "/#"))
                    self._text_file.is_changed = True
                    logger.warning(
                        f"В файле {self._text_file.rel_path} некорректная ссылка:\n"
                        f"{_}\n"
                        f"Строка: {link.index}", result=True)

                else:
                    continue

        if self._text_file.is_changed is False:
            logger.debug(f"file {self._text_file.rel_path}, no missing slashes to fix")

    def fix_links(self):
        """
        Fixing errors and updating the text.

        """
        self._validate()
        self._fix_whitespaces()
        self._fix_missing_slashes_after_dots()
        self._fix_missing_slashes_before_hash()


link_fixer: LinkFixer = LinkFixer()
link_fixer.__doc__ = "The instance to fix links."
