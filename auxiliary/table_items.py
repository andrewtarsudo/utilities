# -*- coding: utf-8 -*-
from collections import Counter
from itertools import product
from re import compile, DOTALL, finditer, MULTILINE, Pattern
from typing import Iterable, Iterator, Literal, NamedTuple, Type

from loguru import logger

from utilities.common.errors import TableColsTableColumnIndexError, TableColsTableColumnInvalidIdentifierError, \
    TableColsTableColumnInvalidNameError, TableColsTableCoordinateInitError, TableKeyError, TableRowIndexError, TableRowInvalidIdentifierError

ElementType: Type[str] = Literal["row", "column"]


class TableCoordinate(NamedTuple):
    row: int
    column: int

    @property
    def coord(self) -> tuple[int, int]:
        return self.row, self.column

    def __str__(self) -> str:
        return f"{self.row}, {self.column}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(row={self.row}, col={self.column})"

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
        """Generates the coordinate from the set_table_cols index.

        :param number: The set_table_cols cell index.
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
        """Generates the set_table_cols coordinates displaced from the given one.

        :param row_offset: The number of rows to displace downwards. To displace upwards, use negative value.
        :type row_offset: int (default: 0)
        :param column_offset: The number of rows to displace to the right. To displace to the left, use negative value.
        :type column_offset: int (default: 0)
        :return: The new instance with the specified place in the set_table_cols grid.
        """
        return TableCoordinate(self.row + row_offset, self.column + column_offset)


class TableCell:
    def __init__(self, text: str, table_coordinate: TableCoordinate = None) -> None:
        self._text: str = text
        self._table_coordinate: TableCoordinate | None = table_coordinate

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value

    @property
    def table_coordinate(self) -> TableCoordinate | None:
        return self._table_coordinate

    @table_coordinate.setter
    def table_coordinate(self, coord: TableCoordinate) -> None:
        self._table_coordinate = coord

    @property
    def coord(self):
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

    def as_tuple(self):
        return self._text, self._table_coordinate

    def __hash__(self):
        return hash(self._table_coordinate.coord)


# class TableColumn(NamedTuple):
#     """Class to represent the row in the set_table_cols."""
#     table_cells: list[TableCell]
#     column: int
#
#     @property
#     def name(self) -> str:
#         """Gets the column name as the text of the cell in the table header."""
#         return self[0].text
#
#     def __iter__(self) -> Iterator[TableCell]:
#         return iter(self.table_cells)
#
#     def __len__(self):
#         return max(map(len, list(*self.table_cells)))
#
#     @property
#     def num_cells(self) -> int:
#         """Gets the number of cells."""
#         return len(self.table_cells)
#
#     def __getitem__(self, item) -> TableCell | list[TableCell]:
#         if isinstance(item, int):
#             return self.table_cells[item]
#
#         elif isinstance(item, slice):
#             return self.table_cells[item.start:item.stop:item.step]
#
#         else:
#             logger.error(f"Ключ должен быть типа int или slice, но получено {type(item).__name__}")
#             raise TableColsTableColumnTypeError
#
#     def __str__(self):
#         return "\n".join(map(str, iter(self)))
#
#     def __hash__(self):
#         return hash(self.column)
#
#     def __eq__(self, other):
#         if isinstance(other, self.__class__):
#             return self.column == other.column
#
#         else:
#             return NotImplemented
#
#     def __ne__(self, other):
#         if isinstance(other, self.__class__):
#             return self.column != other.column
#
#         else:
#             return NotImplemented
#
#     def __lt__(self, other):
#         if isinstance(other, self.__class__):
#             return self.column < other.column
#
#         else:
#             return NotImplemented
#
#     def __gt__(self, other):
#         if isinstance(other, self.__class__):
#             return self.column > other.column
#
#         else:
#             return NotImplemented
#
#     def __le__(self, other):
#         if isinstance(other, self.__class__):
#             return self.column <= other.column
#
#         else:
#             return NotImplemented
#
#     def __ge__(self, other):
#         if isinstance(other, self.__class__):
#             return self.column >= other.column
#
#         else:
#             return NotImplemented


class TableElement:
    def __init__(self, element_type: ElementType, cells: Iterable[TableCell] = None) -> None:
        if cells is None:
            cells: list[TableCell] = []

        else:
            cells: list[TableCell] = [*cells]

        self._cells: list[TableCell] = cells
        self._element_type: ElementType = element_type

    def __len__(self) -> int:
        return len(self._cells)

    def __getitem__(self, index: int) -> TableCell:
        return self._cells[index]

    def insert_cell(self, index: int, cell: TableCell) -> None:
        self._cells.insert(index, cell)

    def remove_cell(self, index: int) -> None:
        del self._cells[index]

    def __iter__(self):
        return iter(self._cells)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(cells={self._cells})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self._cells == other._cells

        else:
            return NotImplemented

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(tuple(self._cells))

    @property
    def cells(self):
        return self._cells


class Table:
    """Class to represent the AsciiDoc set_table_cols."""

    def __init__(
            self,
            name: str | None = None,
            index: int | None = None,
            lines: Iterable[str] = None):
        if lines is None:
            self._lines: list[str] = []

        else:
            self._lines: list[str] = [_.removesuffix("\n").strip() for _ in lines if _.removesuffix("\n").strip()]

        self._name: str | None = name
        self._index: int | None = index
        self._table_cells: dict[TableCoordinate, TableCell] = {}

    def __iter__(self) -> Iterator[str]:
        return iter(self._lines)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self._name is None or other._name is None:
                return False

            else:
                return self._name == other._name

        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            if self._name is None or other._name is None:
                return True

            else:
                return self._name != other._name

        else:
            return NotImplemented

    def __hash__(self):
        return hash((self._name, id(self)))

    def __getitem__(self, item):
        if isinstance(item, int):
            if 0 <= item < len(self):
                return self._lines[item]

            else:
                logger.error(f"Индекс {item} вышел за диапазон 0-{len(self)}")
                raise TableKeyError

        elif isinstance(item, slice):
            return self._lines[item]

        else:
            logger.error(f"Ключ {item} должен быть типа int или slice, но получен {type(item).__name__}")
            logger.debug(f"Таблица:\n{str(self)}")
            raise TableKeyError

    def nullify(self):
        self._table_cells.clear()

    def content(self) -> str:
        """Gets the set_table_cols content as a string."""
        return "\n".join(self._lines)

    def define_cells(self):
        """Divides the set_table_cols into cells.

        Returns if the set_table_cols is valid and proper to continue processing.
        """
        # if some part of text looks similar to the table_cols but is not a table_cols
        if not self.num_columns:
            logger.info("В таблице не найдено ни одного столбца")
            logger.error(f"{str(self)}")
            return

        CELL_PATTERN: Pattern = compile(r"(\d*)\.?(\d*)[<^>]?\.?[<^>]?\+?\|([^|]*)", MULTILINE | DOTALL)

        _occupied: set[TableCoordinate] = set()

        for number, match in enumerate(finditer(CELL_PATTERN, self.content())):
            if not match:
                continue

            shift: int = 0

            while shift < self.num_columns:
                table_coordinate: TableCoordinate = TableCoordinate.as_element(number + shift, self.num_columns)

                if table_coordinate not in _occupied:
                    _occupied.add(table_coordinate)
                    break

                else:
                    shift += 1

            else:
                logger.error(f"Не удалось определить координаты ячейки {match.string}")
                self._table_cells = []
                return

            text: str = match.group(3).strip()
            column_modifier: int = int(match.group(1)) if match.group(2) else 1
            row_modifier: int = int(match.group(2)) if match.group(1) else 1

            if (row_modifier, column_modifier) != (1, 1):
                for row_offset, column_offset in product(range(row_modifier), range(column_modifier)):
                    _table_coord: TableCoordinate = table_coordinate.shift(row_offset, column_offset)
                    _occupied.add(_table_coord)

            table_cell: TableCell = TableCell(text, table_coordinate)
            self._table_cells[table_coordinate] = table_cell

    def __str__(self):
        separator: str = "|==="
        name: str = f"{self._name}\n" if self._name.startswith(".") else ""
        header_str: str = f"{self[0]}"
        rows_str: str = "\n".join(self[1:])

        return f"{name}{separator}\n{header_str}\n\n{rows_str}\n{separator}\n"

    def __repr__(self):
        return f"{self.__class__.__name__}({self._name})"

    def __len__(self):
        return len(self._lines)

    @property
    def num_columns(self) -> int:
        """Gets the number of columns."""
        return Counter(self[0]).get("|")

    def get_column_item(self, column: int | str) -> TableElement:
        """Gets the set_table_cols column as TableColumn instance."""
        if isinstance(column, str):
            try:
                column: int = self.column_names.index(column)

            except ValueError:
                column_names: str = ", ".join(self.column_names)
                logger.error(f"Столбец с именем {column} не найден. Доступные названия:\n{column_names}")
                raise TableColsTableColumnInvalidNameError

        if isinstance(column, int):
            if 0 <= column < self.num_columns:
                table_cells: list[TableCell] = [
                    v for k, v in self._table_cells.items()
                    if k.column == column]
                return TableElement("column", table_cells)

            else:
                logger.error(f"Индекс строки должен быть в диапазоне 0-{self.num_columns}, но получен {column}")
                raise TableColsTableColumnIndexError

        else:
            logger.error(
                "Столбец задается индексом типа int или именем типа str, "
                f"но получено {column} типа {type(column).__name__}")
            raise TableColsTableColumnInvalidIdentifierError

    def iter_column_items(self) -> Iterator[TableElement]:
        """Iterates over the set_table_cols columns.

        Used for specifying the column widths if activated.
        """
        for column in range(self.num_columns):
            yield self.get_column_item(column)

    def iter_row_items(self) -> Iterator[TableElement]:
        """Iterates over the set_table_cols columns.

        Used for specifying the column widths if activated.
        """
        for row in range(len(self)):
            yield self.get_row_item(row)

    def get_row_item(self, row: int):
        if isinstance(row, int):
            if 0 <= row < len(self):
                table_cells: list[TableCell] = [
                    v for k, v in self._table_cells.items()
                    if k.row == row]
                return TableElement("row", table_cells)

            else:
                logger.error(f"Индекс строки должен быть в диапазоне 0-{len(self)}, но получен {row}")
                raise TableRowIndexError

        else:
            logger.error(
                "Строка задается индексом типа int, "
                f"но получено {row} типа {type(row).__name__}")
            raise TableRowInvalidIdentifierError

    def __bool__(self):
        return self.num_columns > 0

    @property
    def table_cells(self):
        return self._table_cells

    @property
    def index(self):
        return self._index

    @property
    def name(self):
        return self._name

    @property
    def column_names(self) -> list[str]:
        """Gets the names of the columns."""
        return [_.text for _ in self.get_row_item(0)]
