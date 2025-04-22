# -*- coding: utf-8 -*-
from pathlib import Path

from click.utils import get_app_dir
from loguru import logger

from utilities.common.functions import file_reader, file_writer, GitFile
from utilities.terms.version_container import Version, VersionContainer


class GitManager:
    TEMPORARY: Path = Path(get_app_dir("utilities"))
    TEMPORARY_TERMS: Path = TEMPORARY.joinpath("terms")

    TEMP_VERSION: Path = TEMPORARY.joinpath("__version__.txt")
    TEMP_TERMS_VERSION: Path = TEMPORARY_TERMS.joinpath("__version__.txt")
    TEMP_TERMS: Path = TEMPORARY.joinpath("terms.adoc")
    TEMP_TERMS_BASIC: Path = TEMPORARY_TERMS.joinpath("terms.adoc")

    def __init__(self):
        self._lines: list[str] = []
        self._version_validator: VersionContainer = VersionContainer(self.TEMP_VERSION, self.TEMP_TERMS_VERSION)
        self._content_git_terms: GitFile | None = None
        self._content_git_version: GitFile | None = None

        self.TEMPORARY_TERMS.mkdir(parents=True, exist_ok=True)

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

    def set_content_git_pages(self):
        content_git_terms: GitFile = GitFile("terms.adoc", 57022544)
        content_git_terms.download()
        self._content_git_terms = content_git_terms

        content_git_version: GitFile = GitFile("__version__.txt", 57022544)
        content_git_version.download()
        self._content_git_version = content_git_version

    def set_versions(self):
        self._version_validator.set_version_basic()
        content: str = file_reader(self._content_git_version.download_destination, "string")
        self._version_validator.version = Version.from_string(content)

    def compare(self):
        self.set_versions()

        if self._version_validator.version_basic == Version("0", "0", "0"):
            message: str = "Версия не определена"

        elif not bool(self):
            message: str = "Версия не последняя"

        elif not Path(self.TEMP_TERMS_BASIC).exists():
            message: str = "Файл с терминами не найден"

        else:
            logger.debug("Версия актуальна")
            return

        logger.error(message)
        file_writer(self.TEMP_TERMS_VERSION, self._content_git_version.content)
        logger.debug("Файл с версией записан")

    def set_terms(self):
        file_writer(self.TEMP_TERMS_BASIC, self._content_git_terms.content)
        lines: list[str] = file_reader(self.TEMP_TERMS_BASIC, "lines", encoding="utf-8")
        self._lines = lines[6:-1]

    def __iter__(self):
        return iter(self._lines)


git_manager: GitManager = GitManager()
