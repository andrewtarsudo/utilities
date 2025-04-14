# -*- coding: utf-8 -*-
from re import DOTALL, sub
from string import ascii_letters, digits

from slugify import slugify

from utilities.common.shared import FileType, TextType
from utilities.table_cols.coordinate import TableCoordinate


class TableCell:
    """Class to represent the table_cols cell."""
    file_type: TextType

    def __init__(
            self,
            table_coordinate: TableCoordinate,
            text: str = None,
            row_modifier: int = 1,
            column_modifier: int = 1):
        self._table_coordinate: TableCoordinate = table_coordinate
        self._text: str = text
        self._row_modifier: int = row_modifier
        self._column_modifier: int = column_modifier

    def __hash__(self):
        return hash(self._table_coordinate.coord)

    @property
    def occupied_elements(self) -> int:
        """Gets the number of real cells united to this one with spans."""
        return self._row_modifier * self._column_modifier

    def __bool__(self):
        return self._text is not None and bool(self._text)

    @property
    def coord(self) -> tuple[int, int]:
        """Gets the coordinates."""
        return self._table_coordinate.coord

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.coord == other.coord

        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self.coord != other.coord

        else:
            return NotImplemented

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f"{self._table_coordinate.__class__.__name__}({self._table_coordinate})\n{self._text}")

    def __str__(self) -> str:
        if not bool(self):
            return "| "

        else:
            return f"|{self._text}"

    def __contains__(self, item):
        return str(item) in self._text

    @property
    def text(self):
        return self._text
