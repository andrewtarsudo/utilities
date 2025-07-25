# -*- coding: utf-8 -*-
from typing import Any, Callable, NamedTuple


def check_bool(func: Callable):
    def wrapper(obj: Any, *args, **kwargs):
        if bool(obj):
            return "Не найдено"

        else:
            return func(obj, *args, **kwargs)

    return wrapper


class Term(NamedTuple):
    short: str | None = None
    full: str | None = None
    rus: str | None = None
    commentary: str | None = None

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}"
            f"(short={self.short}, full={self.full}, rus={self.rus}, commentary={self.commentary})>")

    def __str__(self):
        return f"{self.short}\n{self.full}, {self.rus} -- {self.commentary}"

    def __bool__(self):
        return all(not v for v in self._asdict().values())

    def _formatting_type(self) -> int:
        """1 * bool(full) + 2 * bool(rus) + 4 * bool(commentary)"""

        def _multiplier(attr: str) -> int:
            value: str = getattr(self, attr)
            return int(value is not None and not (not value))

        _: dict[str, int] = {
            "full": 1,
            "rus": 2,
            "commentary": 4}

        return sum(map(lambda x: _multiplier(x) * _.get(x), _.keys()))

    def _formatting_description(self) -> str:
        _: dict[int, str] = {
            1: f"{self.full}",
            2: f"{self.rus}",
            3: f"{self.full}, {self.rus}",
            4: f"{self.commentary}",
            5: f"{self.full} -- {self.commentary}",
            6: f"{self.rus} -- {self.commentary}",
            7: f"{self.full}, {self.rus} -- {self.commentary}"}

        return _.get(self._formatting_type(), "")

    @check_bool
    def abbr(self) -> str:
        return f"<abbr title=\"{self.full}\">{self.short}</abbr>"

    @check_bool
    def ascii_doc(self) -> str:
        return f":{self.short.lower()}: pass:[<abbr title=\"{self.full}\">{self.short}</abbr>]"

    @check_bool
    def formatted(self) -> str:
        return f"{self.short}\n{self._formatting_description()}"


class Coordinate(NamedTuple):
    row_index: int
    column_index: int

    def __str__(self):
        return f"({self.row_index}, {self.column_index})"

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.row_index}, {self.column_index})>"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self.row_index, self.column_index) == (other.row_index, other.column_index)

        else:
            return False

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return (self.row_index, self.column_index) != (other.row_index, other.column_index)

        else:
            return False

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        elif self.row_index == other.row_index:
            return self.column_index < other.column_index

        elif self.column_index == other.column_index:
            return self.row_index < other.row_index

        else:
            return False

    def __gt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        elif self.row_index == other.row_index:
            return self.column_index > other.column_index

        elif self.column_index == other.column_index:
            return self.row_index > other.row_index

        else:
            return False

    def __le__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        elif self.row_index == other.row_index:
            return self.column_index <= other.column_index

        elif self.column_index == other.column_index:
            return self.row_index <= other.row_index

        else:
            return False

    def __ge__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        elif self.row_index == other.row_index:
            return self.column_index >= other.column_index

        elif self.column_index == other.column_index:
            return self.row_index >= other.row_index

        else:
            return False

    def __bool__(self):
        return (self.row_index, self.column_index) == (-1, -1)


class TableItem(NamedTuple):
    row_index: int = -1
    column_index: int = -1
    text: str | None = None

    @property
    def coord(self) -> Coordinate:
        return Coordinate(self.row_index, self.column_index)

    def __str__(self):
        return f"{self.text}"

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.row_index}, {self.column_index}, {self.text})>"

    def __bool__(self):
        return bool(self.text)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.coord == other.coord

        else:
            return False

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self.coord != other.coord

        else:
            return False

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.coord < other.coord

        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.coord > other.coord

        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, self.__class__):
            return self.coord <= other.coord

        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, self.__class__):
            return self.coord >= other.coord

        else:
            return NotImplemented
