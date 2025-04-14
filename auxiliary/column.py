# -*- coding: utf-8 -*-
from typing import Iterator, NamedTuple

from loguru import logger

from utilities.common.errors import TableColsTableColumnTypeError
from auxiliary.cell import TableCell


class TableColumnParameters(NamedTuple):
    """Class to represent the main parameters to define the table_cols column widths.

    :param index: The 0-based column index in the table_cols.
    :type index: int
    :param minimum_length: The minimum length of the cell texts to avoid unpredictable hyphenation.
    :type minimum_length: int
    :param preferred_length: The maximum length of the cell texts to display them in single lines.
    :type preferred_length: int
    :param is_spaced: The flag if the cell texts have any spaces.
    :type is_spaced: bool
    """
    index: int
    minimum_length: int
    preferred_length: int
    is_spaced: bool

    def __str__(self):
        return (
            f"Столбец {self.index}\n"
            f"Минимальная ширина: {self.minimum_length}\n"
            f"Предпочтительная ширина: {self.preferred_length}\n"
            f"Содержит только неразрывный текст: {not self.is_spaced}")

    def __repr__(self):
        return f"<{self.__class__.__name__}({self._asdict()})>"

    def __hash__(self):
        return hash(self.index)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.index == other.index

        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self.index != other.index

        else:
            return NotImplemented

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.index < other.index

        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.index > other.index

        else:
            return NotImplemented


class TableColumn(NamedTuple):
    """Class to represent the row in the table_cols."""
    table_cells: list[TableCell]
    column: int

    @property
    def name(self) -> str:
        """Gets the column name as the text of the cell in the table header."""
        return self[0].text

    def __iter__(self) -> Iterator[TableCell]:
        return iter(self.table_cells)

    def __len__(self):
        return max(map(len, self.table_cells))

    @property
    def num_cells(self) -> int:
        """Gets the number of cells."""
        return len(self.table_cells)

    def __getitem__(self, item) -> TableCell | list[TableCell]:
        if isinstance(item, int):
            return self.table_cells[item]

        elif isinstance(item, slice):
            return self.table_cells[item.start:item.stop:item.step]

        else:
            logger.error(f"Ключ должен быть типа int или slice, но получено {type(item)}")
            raise TableColsTableColumnTypeError

    def is_spaced(self):
        """Indicates if the column has any cell with a space.

        Header cells are ignored since they cannot indicate
        if the column contains texts to display in the single lines.
        """
        return any(table_cell.is_spaced() for table_cell in self.table_cells[1:])

    def minimum_length(self) -> int:
        """Gets the maximum 'minimum_length' of cells."""
        return max(table_cell.minimum_length for table_cell in iter(self))

    def __str__(self):
        return "\n".join(map(str, iter(self)))

    def preferred_length(self) -> int:
        """Gets the maximum 'preferred_length' of cells."""
        return max(table_cell.preferred_length for table_cell in iter(self))

    def __hash__(self):
        return hash(self.column)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.column == other.column

        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self.column != other.column

        else:
            return NotImplemented

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.column < other.column

        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.column > other.column

        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, self.__class__):
            return self.column <= other.column

        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, self.__class__):
            return self.column >= other.column

        else:
            return NotImplemented

    def column_parameters(self):
        return TableColumnParameters(self.column, self.minimum_length(), self.preferred_length(), self.is_spaced())
