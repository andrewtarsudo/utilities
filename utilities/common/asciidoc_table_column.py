# -*- coding: utf-8 -*-
from typing import Iterator, NamedTuple

from loguru import logger

from utilities.common.asciidoc_table_cell import TableCell
from utilities.common.errors import TableColsTableColumnTypeError


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

    def __str__(self):
        return "\n".join(map(str, iter(self)))

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
