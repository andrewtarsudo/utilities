# -*- coding: utf-8 -*-
from pathlib import Path

from click.utils import get_app_dir
from loguru import logger

from utilities.common.functions import file_reader, file_writer, ReaderMode
from utilities.terms.content_git_page import ContentGitPage
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
        self._content_git_terms: ContentGitPage | None = None
        self._content_git_version: ContentGitPage | None = None

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
        content_git_terms: ContentGitPage = ContentGitPage(
            file_name="terms.adoc",
            path=self.TEMP_TERMS,
            content=[])
        content_git_terms.download()
        self._content_git_terms = content_git_terms

        content_git_version: ContentGitPage = ContentGitPage(
            file_name="__version__.txt",
            path=self.TEMP_VERSION,
            content=[])
        content_git_version.download()
        self._content_git_version = content_git_version

    def set_versions(self):
        self._version_validator.set_version_basic()
        self._version_validator.version = Version.from_string("".join(self._content_git_version.content))

    def output_if_different(self, message: str):
        logger.info(message)
        file_writer(self.TEMP_TERMS_VERSION, self._content_git_version.content)
        logger.debug("Файл с версией записан")

    def compare(self):
        self.set_versions()

        if self._version_validator.version_basic == Version("0", "0", "0"):
            self.output_if_different("Версия не определена")

        elif not bool(self):
            self.output_if_different("Версия не последняя")

        elif not Path(self.TEMP_TERMS_BASIC).exists():
            self.output_if_different(f"Файл с терминами не найден")

        else:
            logger.info(f"Версия актуальна")

    def set_terms(self):
        file_writer(self.TEMP_TERMS_BASIC, self._content_git_terms.content)
        lines: list[str] = file_reader(self.TEMP_TERMS_BASIC, ReaderMode.LINES, encoding="cp1251")
        self._lines = lines[6:-1]

    def __iter__(self):
        return iter(self._lines)


git_manager: GitManager = GitManager()
