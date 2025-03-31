# -*- coding: utf-8 -*-
from bisect import bisect_left
from re import fullmatch
from typing import Iterable

from loguru import logger
from more_itertools import pairwise

from utilities.common.shared import StrPath
from utilities.common.errors import (
    TermsAsciiDocFileTableRowIndexError,
    TermsEmptyFileError,
    TermsInvalidTermIndexError,
)
from utilities.common.functions import file_reader, ReaderMode
from utilities.terms.table import TableCellCoordinate, TableItem, Term


class AsciiDocTableTerms:
    def __init__(self, lines: Iterable[str] = None):
        self._content: list[str] = [*lines]
        self._items: dict[TableCellCoordinate, TableItem] = dict()
        self._dict_terms: dict[str, tuple[Term, ...]] = dict()

    @classmethod
    def from_file(cls, file_path: StrPath):
        _content: list[str] = file_reader(
            file_path, ReaderMode.LINES, encoding="cp1251"
        )

        if not _content or len(_content) < 6:
            logger.error(f"Файл {file_path} пуст")
            raise TermsEmptyFileError

        else:
            lines: list[str] = _content[6:-1]
            return cls(lines)

    def __str__(self):
        return f"{self._content}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>({self._items.items()})"

    def set_terms(self):
        _: list[Term] = [
            Term(*self._get_row_item(row_index)) for row_index in range(self.max_row)
        ]
        _dict_proxy: dict[str, list[Term]] = dict()

        for term in _:
            term_short: str = term.short

            if term_short not in _dict_proxy:
                _dict_proxy[term_short] = []

            _dict_proxy[term_short].append(term)

        _dict_terms: dict[str, tuple[Term, ...]] = {
            k.upper(): (*v,) for k, v in _dict_proxy.items()
        }
        self._dict_terms.update(**_dict_terms)

        logger.debug("Файл обработан успешно")

    def __getitem__(self, item):
        if isinstance(item, str):
            return self._binary_search(item.upper())

        elif isinstance(item, int):
            _term_short: str | None = self._index_to_key(item)

            if _term_short is not None:
                return self._dict_terms.get(_term_short)

            else:
                logger.error(f"Термин с индексом {item} не найден")
                raise TermsInvalidTermIndexError

        else:
            logger.debug(f"Термин {item} не найден")
            return (Term(),)

    def get(self, item):
        return self.__getitem__(item)

    def __contains__(self, item):
        if isinstance(item, str):
            return item in self._dict_terms

        else:
            return False

    def __len__(self):
        return len(self._dict_terms)

    def __iter__(self):
        return iter(self._dict_terms.keys())

    @property
    def _keys(self):
        return list(iter(self))

    def _index_to_key(self, index: int | None):
        return self._keys[index] if index is not None else None

    def terms_short(self) -> tuple[str, ...]:
        return tuple(map(lambda x: x.upper(), iter(self)))

    def _binary_search(
        self, search_value: str, min_index: int = 0, max_index: int = None
    ) -> tuple[Term, ...]:
        """
        Specifies the binary search to accelerate the common one.

        :param str search_value: the value to search
        :param int min_index: the lower bound, default = 0
        :param max_index: the higher bound, default = len(values)
        :return: the searched value position in the list if the value is in the list.
        :rtype: tuple[Term, ...]
        """
        if max_index is None:
            max_index: int = len(self)

        _index: int = bisect_left(self._keys, search_value, min_index, max_index)
        _term_short: str = self._index_to_key(_index)

        if _index != max_index and _term_short == search_value:
            return self._dict_terms.get(_term_short)

        else:
            return Term()

    def _get_row_item(self, row_index: int) -> list[str | None]:
        return [v.text for v in self._get_row(row_index)]

    def _get_row(self, row_index: int) -> list[TableItem]:
        if row_index > self.max_row:
            logger.error(
                f"Индекс строки {row_index} превышает максимально возможное значение"
            )
            raise TermsAsciiDocFileTableRowIndexError

        else:
            return [v for k, v in self._items.items() if k.row_index == row_index]

    @property
    def max_row(self) -> int:
        return max(_.row_index for _ in self._items.keys())

    def _find_header(self) -> int:
        HEADER_PATTERN: str = r"\|(.*)\|(.*)\|(.*)\|(.*)\n"

        for index, line in enumerate(iter(self._content)):
            if fullmatch(HEADER_PATTERN, line):
                return index

        else:
            return 2

    def complete(self):
        header_line: str = self._content[self._find_header()]
        _: list[str] = header_line.split("|")

        _empty: list[int] = [
            index for index, line in enumerate(self._content) if line == "\n"
        ]

        for row_index, (_from, _to) in enumerate(pairwise(_empty[1:-1])):
            lines: list[str] = [
                content.strip("\n") for content in self._content[_from + 1 : _to]
            ]
            _: list[str] = "".join(lines).split("|")

            for column_index, text in enumerate(_[1:]):
                _key: TableCellCoordinate = TableCellCoordinate(row_index, column_index)
                _value: TableItem = TableItem(row_index, column_index, text.strip("|"))
                self._items[_key] = _value

        logger.debug(f"Словарь {self.__class__.__name__} инициализирован")

    @property
    def dict_terms(self):
        return self._dict_terms
