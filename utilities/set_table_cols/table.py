# -*- coding: utf-8 -*-
from collections import Counter
from itertools import product
from re import compile, DOTALL, finditer, MULTILINE
from string import digits
from typing import Iterable, Iterator, Mapping, Pattern

from loguru import logger

from utilities.common.errors import TableColsTableColumnIndexError, TableColsTableColumnInvalidIdentifierError, \
    TableColsTableColumnInvalidNameError
from utilities.set_table_cols.cell import TableCell
from utilities.set_table_cols.column import TableColumn
from utilities.set_table_cols.coordinate import TableCoordinate


class Table:
    """Class to represent the AsciiDoc set_table_cols."""

    def __init__(
            self,
            name: str | None = None,
            index: int | None = None,
            lines: Iterable[str] = None,
            options: Mapping[str, str | None] = None):
        if lines is None:
            self._lines: list[str] = []

        else:
            self._lines = [_.removesuffix("\n").strip() for _ in lines if _.removesuffix("\n").strip()]

        if options is None:
            options: dict[str, str | None] = {}

        self._name: str | None = name
        self._index: int | None = index
        self._options: dict[str, str | None] = {**options}
        self._table_cells: dict[TableCoordinate, TableCell] = {}

    def has_horizontal_span(self):
        """Detects if the set_table_cols has span cells.

        At the time such tables are skipped since they require separate algorithm to determine the rows.
        """
        return any(
            line.strip().startswith(digits)
            for line in iter(self))

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
                raise IndexError

        elif isinstance(item, slice):
            return self._lines[item]

        else:
            logger.error(f"Ключ {item} должен быть типа int или slice, но получен {type(item).__name__}")
            logger.debug(f"Таблица:\n{str(self)}")
            raise TypeError

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

            table_cell: TableCell = TableCell(table_coordinate, text)
            self._table_cells[table_coordinate] = table_cell

    def options_str(self) -> str:
        """Gets the string of set_table_cols options."""
        if not self._options:
            return ""

        else:
            options: list[str] = []

            for k, v in self._options.items():
                # if option has a format 'key="value"'
                if v is not None:
                    options.append(f'{k}="{v}"')

                # if option has a format '%key'
                else:
                    options.append(f"{k}")

            options_str: str = ",".join(options)
            return f"[{options_str}]\n"

    def __str__(self):
        separator: str = "|==="
        name: str = f"{self._name}\n" if self._name.startswith(".") else ""
        header_str: str = f"{self[0]}"
        rows_str: str = "\n".join(self[1:])

        return f"{name}{self.options_str()}{separator}\n{header_str}\n\n{rows_str}\n{separator}\n"

    def __repr__(self):
        return f"{self.__class__.__name__}({self._name})"

    def __len__(self):
        return len(self._lines)

    @property
    def num_columns(self) -> int:
        """Gets the number of columns."""
        return Counter(self[0]).get("|")

    def get_column_item(self, column: int | str) -> TableColumn | None:
        """Gets the set_table_cols column as TableColumn instance."""
        if isinstance(column, int):
            if 0 <= column < self.num_columns:
                table_cells: list[TableCell] = [
                    v for k, v in self._table_cells.items()
                    if k.column == column]
                return TableColumn(table_cells, column)

            else:
                logger.error(f"Индекс строки должен быть в диапазоне 0-{self.num_columns}, но получен {column}")
                raise TableColsTableColumnIndexError

        elif isinstance(column, str):
            if column in self.column_names:
                for column_item in self.iter_column_items():
                    if column_item.name == column:
                        return column_item

            else:
                column_names: str = ", ".join(self.column_names)
                logger.error(f"Столбец с именем {column} не найден. Доступные названия:\n{column_names}")
                raise TableColsTableColumnInvalidNameError

        else:
            logger.error(
                "Столбец задается индексом типа int или именем типа str, "
                f"но получено {column} типа {type(column).__name__}")
            raise TableColsTableColumnInvalidIdentifierError

    def iter_column_items(self) -> Iterator['TableColumn']:
        """Iterates over the set_table_cols columns.

        Used for specifying the column widths if activated.
        """
        for column in range(self.num_columns):
            yield self.get_column_item(column)

    def __bool__(self):
        return self.num_columns > 0

    @property
    def table_cells(self):
        return self._table_cells

    @property
    def options(self):
        return self._options

    @property
    def index(self):
        return self._index

    @property
    def name(self):
        return self._name

    @property
    def column_names(self) -> list[str]:
        """Gets the names of the columns."""
        return [_.name for _ in self.iter_column_items()]
