# -*- coding: utf-8 -*-
from pathlib import Path

from loguru import logger

from terms.const import write_file, read_file, _temp_terms_basic, _temp_terms_version
from terms.content_git_page import content_git_terms, content_git_version
from terms.version_container import VersionContainer, Version


class GitManager:
    def __init__(self):
        self._lines: list[str] = []
        self._version_validator: VersionContainer = VersionContainer()

    def __str__(self):
        return f"<{self.__class__.__name__}>"

    __repr__ = __str__

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

    def __bool__(self):
        return bool(self._version_validator)

    @property
    def version_validator(self):
        return self._version_validator

    @version_validator.setter
    def version_validator(self, value):
        self._version_validator = value

    def set_versions(self):
        self._version_validator.set_version_basic()
        content_git_version.download()
        self._version_validator.version = Version.from_string("".join(content_git_version.content))

    def compare(self):
        self.set_versions()

        if self._version_validator.version_basic == Version("0", "0", "0"):
            logger.info(f"Версия не определена")
            write_file(_temp_terms_version, content_git_version.content)
            logger.debug(f"Файл с версией записан")

        elif not bool(self):
            logger.info(f"Версия не последняя")
            write_file(_temp_terms_version, content_git_version.content)
            logger.debug(f"Файл с версией записан")

        elif not Path(_temp_terms_basic).exists():
            logger.info(f"Файл с терминами не найден")
            write_file(_temp_terms_version, content_git_version.content)

        else:
            logger.info(f"Версия актуальна")

    @property
    def lines(self):
        return self._lines

    @lines.setter
    def lines(self, value):
        self._lines = value

    def set_terms(self):
        content_git_terms.download()
        write_file(_temp_terms_basic, content_git_terms.content)
        lines: list[str] = read_file(_temp_terms_basic).split("\n")
        self._lines = lines[6:-1]
