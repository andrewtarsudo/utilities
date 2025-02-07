# -*- coding: utf-8 -*-
from typing import NamedTuple

from loguru import logger

from utilities.common.errors import TableColsTableCoordinateInitError


class TableCoordinate(NamedTuple):
    """Class to represent the cell coordinates in the table_cols.

    At the time a bit over-complicated since there is no need to compare or order cells,
    but may be used in other scripts.
    """
    row: int
    column: int

    def __str__(self):
        return f"{self.row},{self.column}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.row}:{self.column})"

    @property
    def coord(self) -> tuple[int, int]:
        return self.row, self.column

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

    @classmethod
    def as_element(cls, number: int, num_columns: int):
        """Generates the coordinate from the table_cols index.

        :param number: The table_cols cell index.
        :type number: int
        :param num_columns: The number of columns.
        :type num_columns: int
        """
        if number >= 0 and num_columns > 0:
            return cls(*divmod(number, num_columns))

        else:
            logger.error(
                f"Индекс {number} и количество столбцов {num_columns} должны быть положительными")
            raise TableColsTableCoordinateInitError

    def shift(self, row_offset: int = 0, column_offset: int = 0):
        """Generates the table_cols coordinates displaced from the given one.

        :param row_offset: The number of rows to displace downwards. To displace upwards, use negative value.
        :type row_offset: int (default: 0)
        :param column_offset: The number of rows to displace to the right. To displace to the left, use negative value.
        :type column_offset: int (default: 0)
        :return: The new instance with the specified place in the table_cols grid.
        """
        return TableCoordinate(self.row + row_offset, self.column + column_offset)
