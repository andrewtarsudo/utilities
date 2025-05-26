# -*- coding: utf-8 -*-
from re import finditer, Match, sub

from loguru import logger

from utilities.common.errors import RepairLinksFixerNoLinkError, RepairLinksInvalidHashCharIndexError
from utilities.repair_links.file_dict import TextFile


class LinkFixer:
    """Class to represent the instance to fix links."""
    PATTERN: str = r"(\.\.)(\w)"

    def __init__(self):
        self.text_file: TextFile | None = None

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
        return self.text_file.iter_links()

    def __bool__(self):
        return self.text_file is not None

    def _validate(self):
        """Inspects if the file is specified."""
        if not bool(self):
            logger.error("Не задан файл")
            raise RepairLinksFixerNoLinkError

    def _fix_whitespaces(self):
        """Fixes errors when the link has whitespaces."""
        for link in iter(self):
            _: str = link.link.link_to

            if " " in _:
                self.text_file.update_line(link.index, _, _.replace(" ", ""))
                logger.warning(
                    f"В файле {self.text_file.rel_path} некорректная ссылка:"
                    f"\n{_}"
                    f"\nСтрока: {link.index}", result=True)

        if self.text_file.is_changed is False:
            logger.debug(f"В файле {self.text_file.rel_path} нет пробелов для исправления")

    def _fix_missing_slashes_after_dots(self):
        """Fixes errors when the link has double dots with no slash followed."""

        def add_slash(match: Match):
            return f"{match.group(1)}/{match.group(2)}"

        for link in iter(self):
            _: str = link.link.link_to

            for _m in finditer(self.__class__.PATTERN, _):
                if _m:
                    self.text_file.update_line(link.index, _, sub(self.__class__.PATTERN, add_slash, _))
                    self.text_file.is_changed = True
                    logger.warning(
                        f"В файле {self.text_file.rel_path} некорректная ссылка:\n"
                        f"{_}\n"
                        f"Строка: {link.index}", result=True)

        if self.text_file.is_changed is False:
            logger.debug(f"В файле {self.text_file.rel_path} нет недостающих '/'")

    def _fix_missing_slashes_before_hash(self):
        """Fixes errors when the link has an anchor with no slash before."""
        for link in iter(self):
            _: str = link.link.link_to

            if bool(link.link):
                index: int = _.find("#") - 1

                if index < -1:
                    logger.error(
                        f"Позиция # в файле {self.text_file.rel_path} в ссылке {_} определена как {index}, "
                        f"что некорректно")
                    raise RepairLinksInvalidHashCharIndexError

                elif index == -1:
                    logger.debug(f"Ссылка {link} внутренняя")
                    continue

                elif _[index] != "/":
                    self.text_file.update_line(link.index, _, _.replace("#", "/#"))
                    self.text_file.is_changed = True
                    logger.warning(
                        f"В файле {self.text_file.rel_path} некорректная ссылка:\n"
                        f"{_}\n"
                        f"Строка: {link.index}", result=True)

                else:
                    continue

        if self.text_file.is_changed is False:
            logger.debug(f"В файле {self.text_file.rel_path} нет недостающих '/'")

    def fix_links(self):
        """Fixes errors and updating the text."""
        self._validate()
        self._fix_whitespaces()
        self._fix_missing_slashes_after_dots()
        self._fix_missing_slashes_before_hash()


link_fixer: LinkFixer = LinkFixer()
link_fixer.__doc__ = "The instance to fix links."
