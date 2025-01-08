# -*- coding: utf-8 -*-
from collections import Counter
from pathlib import Path
from typing import Iterable

from loguru import logger

from repair_link.dir_file import TextFile
from repair_link.general.const import FileLanguage, prepare_logging
from repair_link.general.errors import MissingFileError, FileInvalidTypeError
from repair_link.general.const import separator


class AnchorInspector:
    """
    The inspector for anchors in the files.

    Attributes
    ----------
    _dict_anchors : dict[str, list[str]]
        The dictionary of the files and anchors inside.
    _dict_files : dict[str, list[TextFile]]
        The dictionary of the anchors and the files containing these links.
    _dict_changes : dict[TextFile, list[str]]
        The dictionary of the files and anchors to fix.
    _separate_languages : bool
        The flag to handle the file according to the file languages.

    """
    def __init__(self, separate_languages: bool = True):
        self._dict_anchors: dict[TextFile, list[str]] = dict()
        self._dict_files: dict[str, list[TextFile]] = dict()
        self._dict_changes: dict[TextFile, list[str]] = dict()
        self._separate_languages: bool = separate_languages

    def __str__(self):
        return f"<{self.__class__.__name__}>"

    __repr__ = __str__

    def __getitem__(self, item):
        if isinstance(item, str):
            for text_file in self._dict_anchors.keys():
                if text_file.full_path == Path(item):
                    return text_file

            else:
                logger.error(f"Не найден файл {item}", result=True)
                raise MissingFileError

        else:
            logger.error(f"Ключ {item} должен быть типа str, но получен {type(item)}")
            raise FileInvalidTypeError

    get = __getitem__

    def __add__(self, other):
        if isinstance(other, TextFile):
            other.read()
            self._dict_anchors[other] = list(other.iter_anchors())

        elif isinstance(other, Iterable):
            text_files: list[TextFile] = [_ for _ in other if isinstance(_, TextFile)]

            for text_file in text_files:
                text_file.read()
                self._dict_anchors[text_file] = list(text_file.iter_anchors())

        else:
            logger.error(f"Элемент {other} должен быть типа TextFile, но получен {type(other)}")

    @property
    def dict_anchors(self):
        return self._dict_anchors

    @dict_anchors.setter
    def dict_anchors(self, value):
        self._dict_anchors = value

    @property
    def dict_ru_files(self) -> dict[TextFile, list[str]]:
        """
        The files in Russian.

        Returns
        -------
        dict[TextFile, list[str]]
            The dictionary of Russian files and their anchors.

        """
        return {k: v for k, v in self._dict_anchors.items() if k.language == FileLanguage.RU}

    @property
    def dict_en_files(self) -> dict[TextFile, list[str]]:
        """Gets the files in English.

        :return: The dictionary of English files and their anchors.
        :rtype: dict[TextFile, list[str]]
        """
        return {k: v for k, v in self._dict_anchors.items() if k.language == FileLanguage.EN}

    def _get_files(self, language: FileLanguage) -> dict[TextFile, list[str]]:
        """Gets only necessary files.

        :param language: The language of the text files.
        :type language: FileLanguage
        :return: The dictionary of the text files and their anchors.
        :rtype: dict[TextFile, list[str]]
        """
        if language == FileLanguage.RU:
            return self.dict_ru_files

        elif language == FileLanguage.EN:
            return self.dict_en_files

        else:
            return self._dict_anchors

    def _find_files(self, anchor: str, language: FileLanguage) -> list[TextFile]:
        """Finds the files having the specified anchor.

        :param anchor: The anchor to find in the files.
        :type anchor: str
        :return: The list of files having the specified anchor.
        :rtype: list[str]
        """
        return [k for k, v in self._get_files(language).items() if anchor in v]

    def inspect_inside_file(self, language: FileLanguage):
        """Inspects anchors inside each file.

        :param language: The language of the file.
        :type language: FileLanguage
        """
        for file, anchors in self._get_files(language).items():
            counter: Counter[str] = Counter(anchors)
            _invalid_anchors: list[str] = [k for k, v in counter.items() if v > 1]

            if not _invalid_anchors:
                logger.debug(f"В файле {file} якори корректны")

            else:
                _str_anchors: str = ", ".join(_invalid_anchors)
                logger.error(
                    f"Внутри файла {file} найдены дублирующиеся якори:\n{prepare_logging(_invalid_anchors)}",
                    result=True)

    def all_anchors(self, language: FileLanguage) -> list[str]:
        """Gets all anchors.

        :param language: The language of the file.
        :type language: FileLanguage
        :return: The list of all anchors in all files.
        :rtype: list[str]
        """
        return [anchor for k, v in self._get_files(language).items() for anchor in v]

    def inspect_all_files(self, language: FileLanguage):
        """Inspects anchors through all files.

        :param language: The language of the file.
        :type language: FileLanguage
        """
        counter: Counter = Counter(self.all_anchors(language))
        _invalid_anchors: list[str] = [k for k, v in counter.items() if v > 1]

        if not _invalid_anchors:
            logger.debug(f"Повторяющихся якорей во всех файлах не найдено\n")
            return

        else:
            log_messages: list[str] = []

            for _invalid_anchor in _invalid_anchors:
                _files: list[str] = []

                for file in self._find_files(_invalid_anchor, language):
                    _from: str = _invalid_anchor

                    file: TextFile
                    if file not in self._dict_changes:
                        self._dict_changes[file] = []

                    self._dict_changes[file].append(_from)

                    _files.append(file.rel_path)

                _str_files: str = "\n".join(_files)
                log_messages.append(f"Якорь {_invalid_anchor} повторяется в файлах:\n{_str_files}")

            _str_anchors: str = "\n".join(_invalid_anchors)
            _str_log_messages = f"\n{separator}\n".join(log_messages)

            logger.error(
                f"Найдены повторяющиеся якори:\n{_str_anchors}\n\n"
                f"{_str_log_messages}", result=True)

    @property
    def dict_changes(self):
        return self._dict_changes


anchor_inspector: AnchorInspector = AnchorInspector()
anchor_inspector.__doc__ = "The default anchor inspector."
