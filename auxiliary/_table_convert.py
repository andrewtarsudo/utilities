# -*- coding: utf-8 -*-
from collections import Counter
from itertools import product
from pathlib import Path
from re import compile, DOTALL, finditer, match, Match, MULTILINE, Pattern, search, split, sub, UNICODE, VERBOSE
from typing import Iterable, Iterator, Literal, NamedTuple, Optional, Type

from loguru import logger

from utilities.common.errors import TableColsTableColumnIndexError, TableColsTableColumnInvalidIdentifierError, \
    TableColsTableColumnInvalidNameError
from utilities.common.functions import file_reader, file_writer
from utilities.common.shared import StrPath

TableType: Type[str] = Literal[".md", ".adoc"]
Attrs: Type[str] = Literal["possible_values", "type", "default", "range", "notes"]


class FieldText:
    range_pattern: Pattern = compile(r"\bДиапазон\b(?:[^.|]|<br\s*/?>|\s+\+\n)+\.?", flags=UNICODE)
    type_pattern: Pattern = compile(r"\bТип\b(?:[^.|]|<br\s*/?>|\s+\+\n)+\.?", flags=UNICODE)
    possible_values_pattern: Pattern = compile(r"(?:Возможные значения:|(?<!\.)\G)(?:[^.;|]|<br\s*/?>|\s+\+\n)*?(?:\w+|`\w+`)\s*--?\s*(?:[^.;|]|<br\s*/?>|\s+\+\n)+[.;]?", flags=UNICODE)
    default_pattern: Pattern = compile(r"(?:\bЗначение\b\s)?\b[Пп]о умолчанию\b(?:[^.|]|<br\s*/?>|\s+\+\n)+\.?", flags=UNICODE)

    patterns: dict[Attrs, Pattern] = {
        "possible_values": possible_values_pattern,
        "type": type_pattern,
        "default": default_pattern,
        "range": range_pattern
    }

    replacements: set[str] = {r"\.<br/?>", r"\.\s+", r"\.\s+\+\n"}
    pattern: str = "|".join(replacements)

    __slots__ = ("_content", "_description_text", "_range_text", "_possible_values_text", "_default_text", "_type_text", "_notes_text")

    def __init__(self, content: str):
        self._content: str = content
        self._description_text: str | None = None
        self._possible_values_text: str | None = None
        self._range_text: str | None = None
        self._default_text: str | None = None
        self._type_text: str | None = None
        self._notes_text: list[str] = []

    def getattr(self, attr: Attrs):
        if attr in {"possible_values", "type", "default", "range", "notes"}:
            return self.__getattribute__(f"_{attr}_text")

        else:
            raise KeyError

    def setattr(self, attr: Attrs, value: str | None):
        if self.getattr(attr) is None:
            self.__setattr__(f"_{attr}_text", value)

        else:
            logger.error(f"Атрибуту {attr} уже задано значение")

    def extract_text(self):
        text: str = f"{self._content}"

        for name, pattern in self.patterns.items():
            if m := pattern.search(text):
                self.setattr(name, m.group().strip())
                text.replace(m.group(), "")

            else:
                self.setattr(name, None)

        parts: list[str] = text.split()

        self._description_text = parts.pop(0).strip()
        self._notes_text.extend(part.strip() for part in parts)

    def update_possible_values(self):
        def repl(m: Match):
            return f"{m.group(1)}<br>"

        possible_values: str | None = self.getattr("possible_values")

        if possible_values:
            _: str = sub(r"Возможные значения:?\s+", "Возможные значения:<br>", possible_values)
            _: str = sub(r"([.;])\s", repl, _)

            self.setattr("possible_values", None)
            self.setattr("possible_values", _)

    def stringify(self, attr: Attrs):
        _: str | None = self.getattr(attr)
        return f"<br>{_}" if _ is not None else ""

    # def reorder_text(self):
    #     _: str = sub(self.pattern, ".@@@", self._content)
    #
    #     parts: list[str] = _.split("@@@")
    #
    #     self._description_text = parts.pop(0)
    #
    #     for part in parts:
    #         if part.startswith("Возможные значения"):
    #             self._possible_values.append(part)
    #             continue
    #
    #         m_range: Match = match(self.range_pattern, part)
    #         m_type: Match = match(self.type_pattern, part)
    #         m_default: Match = match(self.default_pattern, part)
    #         m_possible_values: Match = match(self.possible_values_pattern, part)
    #
    #         if m_range:
    #             self._range_text: str = m_range.group()
    #
    #         elif m_type:
    #             self._type_text: str = m_type.group()
    #
    #         elif m_default:
    #             self._default_text: str = m_default.group()
    #
    #         elif m_possible_values:
    #             self._possible_values.append(part)
    #
    #         else:
    #             self._notes_text.append(part)

    def __str__(self):
        return (
            f"{self._description_text}"
            f"{self.stringify("range")}"
            f"{self.stringify("possible_values")}"
            f"{self.stringify("default")}"
            f"<br>{' '.join(self._notes_text)}")


class TableCoordinate(NamedTuple):
    """Class to represent the cell coordinates in the set_table_cols.

    At the time a bit over-complicated since there is no need to compare or order cells,
    but may be used in other scripts.
    """
    row: int
    column: int

    def __str__(self):
        return f"{self.row},{self.column}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>({self.row}:{self.column})"

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
            raise ValueError

    def shift(self, *, row_offset: int = 0, column_offset: int = 0):
        """Generates the set_table_cols coordinates displaced from the given one.

        :param row_offset: The number of rows to displace downwards. To displace upwards, use negative value.
        :type row_offset: int (default: 0)
        :param column_offset: The number of rows to displace to the right. To displace to the left, use negative value.
        :type column_offset: int (default: 0)
        :return: The new instance with the specified place in the set_table_cols grid.
        """
        return TableCoordinate(self.row + row_offset, self.column + column_offset)


class TableCell:
    """Class to represent the set_table_cols cell."""

    def __init__(
            self,
            table_coordinate: TableCoordinate,
            text: str = None,
            row_modifier: int = 1,
            column_modifier: int = 1):
        self._table_coordinate: TableCoordinate = table_coordinate
        self._text: str | None = text
        self._parts: list[str] = []
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
            f"<{self._table_coordinate.__class__.__name__}({self._table_coordinate})>"
            f"\n{self._text}")

    def __str__(self) -> str:
        return f"{self._text}"

    def __len__(self):
        return len(self._text)

    @property
    def text(self):
        return self._text

    @property
    def table_coordinate(self):
        return self._table_coordinate

    @property
    def field_text(self):
        return FieldText(self._text)


class TableRow(NamedTuple):
    """Represents a single row in the table."""
    row: int
    table_cells: list[TableCell]

    def __iter__(self) -> Iterator[TableCell]:
        return iter(self.table_cells)

    def __len__(self):
        return len(self.table_cells)

    def __getitem__(self, item) -> TableCell | list[TableCell]:
        if isinstance(item, int):
            return self.table_cells[item]

        elif isinstance(item, slice):
            return self.table_cells[item.start:item.stop:item.step]

        else:
            logger.error(f"Ключ должен быть типа int или slice, но получено {type(item).__name__}")
            raise TypeError

    def __hash__(self):
        return hash(self.row)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.row == other.row

        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self.row != other.row

        else:
            return NotImplemented

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.row < other.row

        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.row > other.row

        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, self.__class__):
            return self.row <= other.row

        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, self.__class__):
            return self.row >= other.row

        else:
            return NotImplemented

    def __format__(self, format_spec):
        if format_spec == "md":
            cell_str: str = f" | ".join(map(str, self.table_cells))
            return f"| {cell_str} |"

        elif format_spec == "adoc":
            cell_str: str = f" |".join(map(str, self.table_cells))
            return f"|{cell_str}"

        else:
            return super().__format__(format_spec)


class TableColumn(NamedTuple):
    """Class to represent the row in the set_table_cols."""
    column: int
    table_cells: list[TableCell]

    @property
    def name(self) -> str:
        """Gets the column name as the text of the cell in the table header."""
        return self[0].text

    def __iter__(self) -> Iterator[TableCell]:
        return iter(self.table_cells)

    def __len__(self):
        return len(self.table_cells)

    def __getitem__(self, item) -> TableCell | list[TableCell]:
        if isinstance(item, int):
            return self.table_cells[item]

        elif isinstance(item, slice):
            return self.table_cells[item.start:item.stop:item.step]

        else:
            logger.error(f"Ключ должен быть типа int или slice, но получено {type(item).__name__}")
            raise TypeError

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

    @classmethod
    def empty(cls, column: int, num_cells: int):
        table_cells: list[TableCell] = [TableCell(TableCoordinate(row, column)) for row in range(num_cells)]
        return cls(column, table_cells)


def set_subheader_row(num_columns: int):
    _: str = "|-----" * num_columns
    return f"{_}|\n"


def set_cell_text(line: str):
    return line.strip() if line else ""


class Table:
    """Class to represent the AsciiDoc set_table_cols."""
    table_type: TableType
    ADOC_PATTERN: Pattern = compile(r"(\d*)\.?(\d*)[<^>]?\.?[<^>]?\+?\|([^|]*)", MULTILINE | DOTALL)
    MD_PATTERN: Pattern = compile(r"\|")

    def __init__(self, path: StrPath, lines: Iterable[str] = None):
        if lines is None:
            lines: list[str] = []

        else:
            lines: list[str] = [_.removesuffix("\n").strip() for _ in lines if _.removesuffix("\n").strip()]

        self._path: Path = Path(path).expanduser()
        self._lines: list[str] = lines
        self._table_cells: dict[TableCoordinate, TableCell] = {}

    def __iter__(self) -> Iterator[str]:
        return iter(self._lines)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._lines == other._lines

        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self._lines != other._lines

        else:
            return NotImplemented

    def __hash__(self):
        return hash((self._lines, id(self)))

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

    def content(self) -> str:
        """Gets the set_table_cols content as a string."""
        return "\n".join(self._lines)

    @property
    def headers(self) -> list[str]:
        return [cell.text for cell in self.get_row(0)]

    # noinspection PyTypeChecker
    def define_cells(self):
        """Divides the set_table_cols into cells.

        Returns if the set_table_cols is valid and proper to continue processing.
        """
        # if some part of text looks similar to the table_cols but is not a table_cols
        if not self.num_columns:
            logger.info("В таблице не найдено ни одного столбца")
            logger.error(f"{str(self)}")
            return

        _occupied: set[TableCoordinate] = set()

        if self.table_type == ".adoc":
            for number, match in enumerate(finditer(self.__class__.ADOC_PATTERN, self.content())):
                if not match:
                    continue

                shift: int = 0

                while shift < self.num_columns:
                    table_coordinate: TableCoordinate = TableCoordinate.as_element(
                        number + shift,
                        self.num_columns)

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
                        _table_coord: TableCoordinate = table_coordinate.shift(
                            row_offset=row_offset,
                            column_offset=column_offset)
                        _occupied.add(_table_coord)

                table_cell: TableCell = TableCell(table_coordinate, text)
                self._table_cells[table_coordinate] = table_cell

        else:
            for row, line in enumerate(iter(self)):
                texts: list[str] = list(map(set_cell_text, line.strip("|").split("|")))

                for column, text in enumerate(iter(texts)):
                    table_coordinate: TableCoordinate = TableCoordinate(row, column)
                    table_cell: TableCell = TableCell(table_coordinate, text)

                    self._table_cells[table_coordinate] = table_cell

    def __str__(self):
        rows: list[str] = list(map(str, self.iter_rows()))

        if self.table_type == ".md":
            second_row: str = set_subheader_row(self.num_columns)
            boundary: str = ""

        else:
            second_row: str = "\n"
            boundary: str = "|===\n"

        header_str: str = rows[0]
        rows_str: str = "\n".join(rows[1:])

        return f"{boundary}{header_str}\n{second_row}{rows_str}\n{boundary}"

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def __len__(self):
        return len(self._lines)

    @property
    def num_columns(self) -> int:
        """Gets the number of columns."""
        return Counter(self._lines[0].strip("|").strip()).get("|") + 1

    @property
    def num_rows(self) -> int:
        """Gets the number of columns."""
        return max(cell.row for cell in self._table_cells)

    def get_column(self, column: int | str) -> TableColumn:
        """Gets the set_table_cols column as TableColumn instance."""
        if isinstance(column, int):
            if 0 <= column < self.num_columns:
                table_cells: list[TableCell] = [
                    v for k, v in self._table_cells.items()
                    if k.column == column]
                return TableColumn(column, table_cells)

            else:
                logger.error(f"Индекс строки должен быть в диапазоне 0-{self.num_columns}, но получен {column}")
                raise TableColsTableColumnIndexError

        elif isinstance(column, str):
            if column in self.column_names:
                for column_item in self.iter_columns():
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

    def get_row(self, row: int) -> TableRow:
        """Gets the set_table_cols column as TableColumn instance."""
        if isinstance(row, int):
            if 0 <= row < self.num_rows:
                table_cells: list[TableCell] = [
                    v for k, v in self._table_cells.items()
                    if k.row == row]
                return TableRow(row, table_cells)

            else:
                logger.error(f"Индекс строки должен быть в диапазоне 0-{self.num_columns}, но получен {row}")
                raise TableColsTableColumnIndexError

        else:
            logger.error(
                "Строка задается индексом типа int, "
                f"но получено {row} типа {type(row).__name__}")
            raise TableColsTableColumnInvalidIdentifierError

    def add_column(self, table_column: TableColumn):
        if 0 <= table_column.column <= self.num_columns:
            for column in range(table_column.column + 1, self.num_columns):
                for row in range(self.num_rows):
                    table_cell: TableCell = self._table_cells.get(TableCoordinate(row, column))
                    table_cell.table_coordinate.shift(column_offset=1)
                    self._table_cells[table_cell.table_coordinate] = table_cell

            kwargs: dict[TableCoordinate, TableCell] = {cell.table_coordinate: cell for cell in iter(table_column)}
            self._table_cells.update(kwargs)
            self._lines = list(map(str, self.iter_rows()))

        else:
            logger.error(f"Столбец должен быть в диапазоне 0-{self.num_columns}, но получено {table_column.column}")
            return

    def add_row(self, table_row: TableRow):
        if 0 <= table_row.row <= self.num_rows:
            for row in range(table_row.row + 1, self.num_rows):
                for column in range(self.num_columns):
                    table_cell: TableCell = self._table_cells.get(TableCoordinate(row, column))
                    table_cell.table_coordinate.shift(row_offset=1)
                    self._table_cells[table_cell.table_coordinate] = table_cell

            kwargs: dict[TableCoordinate, TableCell] = {cell.table_coordinate: cell for cell in iter(table_row)}
            self._table_cells.update(kwargs)
            self._lines = list(map(str, self.iter_rows()))

        else:
            logger.error(f"Строка должна быть в диапазоне 0-{self.num_rows}, но получено {table_row.row}")
            return

    def remove_column(self, column: int | str):
        if isinstance(column, str):
            try:
                column: int | None = self.column_names.index(column)

            except ValueError:
                column: int | None = None
                logger.error(f"Столбец с названием {column} не найден")
                return

        elif column < 0 or column > self.num_columns:
            logger.error(f"Строка должна быть в диапазоне 0-{self.num_columns}, но получено {column}")
            return

        else:
            pass

        for row in range(self.num_rows):
            table_coordinate: TableCoordinate = TableCoordinate(row, column)
            self._table_cells.pop(table_coordinate)

            for col in range(column + 1, self.num_columns):
                table_cell: TableCell = self._table_cells.get(TableCoordinate(row, col))
                table_cell.table_coordinate.shift(column_offset=-1)
                self._table_cells[table_cell.table_coordinate] = table_cell

        self._lines = list(map(str, self.iter_rows()))

    def remove_row(self, row: int):
        if 0 <= row <= self.num_rows:
            for column in range(self.num_columns):
                table_coordinate: TableCoordinate = TableCoordinate(row, column)
                self._table_cells.pop(table_coordinate)

                for r in range(row + 1, self.num_rows):
                    table_cell: TableCell = self._table_cells.get(TableCoordinate(r, column))
                    table_cell.table_coordinate.shift(row_offset=-1)
                    self._table_cells[table_cell.table_coordinate] = table_cell

            self._lines = list(map(str, self.iter_rows()))

        else:
            logger.error(f"Строка должна быть в диапазоне 0-{self.num_rows}, но получено {row}")
            return

    def iter_columns(self) -> Iterator[TableColumn]:
        """Iterates over the set_table_cols columns.

        Used for specifying the column widths if activated.
        """
        for column in range(self.num_columns):
            yield self.get_column(column)

    def iter_rows(self) -> Iterator[TableRow]:
        """Iterates over the set_table_cols rows.

        Used for specifying the column widths if activated.
        """
        for row in range(self.num_rows):
            yield self.get_row(row)

    def __bool__(self):
        return self.num_columns > 0

    @property
    def table_cells(self):
        return self._table_cells

    @property
    def column_names(self) -> list[str]:
        """Gets the names of the columns."""
        return [_.name for _ in self.iter_columns()]

    def divide_column(self, column: int | str, new_columns: int, splitter: str):
        first_column_cells: list[TableCell] = []
        second_column_cells: list[TableCell] = []

        for row, cell in enumerate(iter(self.get_column(column))):
            first_column_text, second_column_text = cell.text.split(splitter, maxsplit=1)
            first_column_table_coordinate: TableCoordinate = TableCoordinate(row, new_columns + 1)
            second_column_table_coordinate: TableCoordinate = TableCoordinate(row, new_columns + 2)

            first_column_cell: TableCell = TableCell(first_column_table_coordinate, first_column_text)
            second_column_cell: TableCell = TableCell(second_column_table_coordinate, second_column_text)

            first_column_cells.append(first_column_cell)
            second_column_cells.append(second_column_cell)

        first_column: TableColumn = TableColumn(new_columns + 1, first_column_cells)
        second_column: TableColumn = TableColumn(new_columns + 2, second_column_cells)

        self.add_column(first_column)
        self.add_column(second_column)

        self.remove_column(column)

    def split_column(self, column: int | str, pattern: str | Pattern):
        new_column_cells: list[TableCell] = []

        for row, cell in enumerate(iter(self.get_column(column))):
            table_coordinate: TableCoordinate = TableCoordinate(row, column + 1)
            m: Match = search(pattern, cell.text)

            if m:
                text: str = m.group(0)

            else:
                text: str = ""

            new_column_cell: TableCell = TableCell(table_coordinate, text)
            new_column_cells.append(new_column_cell)

        new_column: TableColumn = TableColumn(column + 1, new_column_cells)

        self.add_column(new_column)

    @property
    def is_invalid(self):
        return self.num_columns < 5

    def fix_config(self):
        parameter: TableColumn = self.get_column("Параметр")
        ompr: TableColumn = self.get_column("OMPR")
        description: TableColumn = self.get_column("Описание")

        self.divide_column("OMPR", 3, "/")
        self.split_column("Описание", r"Тип\s.+\s(\w+?)\s?\.?")


class File:
    def __init__(self, path: StrPath):
        self._path: Path = Path(path).expanduser()
        self._content: list[str] = []
        self._tables: dict[str, Table] = {}

    def save(self):
        file_writer(self._path, self._content)

    @property
    def table_type(self):
        return self._path.suffix

    def find_tables(self):
        content: str = file_reader(self._path, "string")
        self._content = content.splitlines(keepends=True)

        if self.table_type == ".md":
            pattern: Pattern = compile(r"^(\|.*\|\s*\n)(?:^\|[\s?:\-]+\|\s*\n)?(^\|.*\|\s*\n?)+", MULTILINE)

        else:
            pattern: Pattern = compile(r"^\s*\|===\s*\n()((?:.*\n)*?)^\s*\|===\s*$", MULTILINE)

        for m in finditer(pattern, content):
            lines: list[str] = [m.group(1).strip(), *m.group(2).splitlines(keepends=True)]

            table: Table = Table(self._path, lines)
            self._tables[m.group(0)] = table


def find_tables(text: str) -> list[str]:
    """
    Finds all Markdown and AsciiDoc tables in the input text and returns them as a list of table strings.
    Markdown tables: header |...|, optional separator |---|..., rows
    AsciiDoc tables: start with |===, end with |===
    """
    tables = []

    # Find Markdown tables (with or without separator)
    md_pattern = compile(
        r'(?:^\s*\|.*\|\s*\n)'  # header
        r'(?:^\s*\|[\s:\-]+\|\s*\n)?'  # optional separator
        r'(?:^\s*\|.*\|\s*\n?)+',  # at least one row
        MULTILINE | VERBOSE
    )
    tables += [match.group(0).strip() for match in md_pattern.finditer(text)]

    # Find AsciiDoc tables
    adoc_pattern = compile(
        r'^\s*\|===\s*\n'  # table start
        r'(?:.*\n)*?'  # table content (non-greedy)
        r'^\s*\|===\s*$',  # table end
        MULTILINE | VERBOSE
    )
    tables += [match.group(0).strip() for match in adoc_pattern.finditer(text)]

    return tables


def read_table(text: str) -> list[dict[str, str]]:
    """
    Parses the input table and returns a list of dicts with keys: Параметр, OMPR, Описание
    Supports both Markdown and AsciiDoc tables.
    """
    # Detect AsciiDoc table
    if text.strip().startswith('|==='):
        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
        # Remove |=== lines
        lines = [line for line in lines if line != '|===']
        if not lines:
            return []
        headers = [h.strip() for h in lines[0].strip('|').split('|')]
        data = []
        for line in lines[1:]:
            if not line.startswith('|'):
                continue
            cells = [c.strip() for c in line.strip('|').split('|')]
            if len(cells) != len(headers):
                continue
            row = dict(zip(headers, cells))
            data.append(row)
        return data
    else:
        # Markdown table
        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
        header_idx = None
        sep_idx = None
        for i, line in enumerate(lines):
            if match(r'^\s*\|', line):
                header_idx = i
                # Accept separator if present, but allow missing
                if i + 1 < len(lines) and match(r'^\s*\|?[\s:-]+\|', lines[i + 1]):
                    sep_idx = i + 1
                else:
                    sep_idx = i  # No separator, data starts right after header
                break
        if header_idx is None or sep_idx is None:
            raise ValueError("Table header or separator not found")

        headers = [h.strip() for h in lines[header_idx].strip('|').split('|')]
        data = []
        for line in lines[sep_idx + 1:]:
            if not line.startswith('|'):
                continue
            cells = [c.strip() for c in line.strip('|').split('|')]
            if len(cells) != len(headers):
                continue
            row = dict(zip(headers, cells))
            data.append(row)
        return data


def extract_type(description: str) -> Optional[str]:
    match = search(r'Тип\s*--\s*(\w+)\.', description)
    return match.group(1) if match else None


def remove_type_sentence(description: str) -> str:
    """
    Removes the sentence 'Тип -- ...' from the description.
    """
    # Remove 'Тип -- ...' sentence (with trailing whitespace)
    return sub(r'Тип\s*--\s*\w+\.\s*', '', description)


def reorder_description(description: str) -> str:
    sentences = split(r'(?<=\.)\s+', description.strip())
    if not sentences:
        return description

    first = sentences[0]
    rest = sentences[1:]

    diapason_idx = next((i for i, s in enumerate(rest) if match(r'Диапазон:\s*\d+-\d+\.', s)), None)
    default_idx = next(
        (i for i, s in enumerate(rest) if match(r'(По умолчанию|Значение по умолчанию)\s*--\s*.+\.', s)), None)

    ordered = [first]
    if diapason_idx is not None:
        ordered.append(rest[diapason_idx])
    if default_idx is not None and default_idx != diapason_idx:
        ordered.append(rest[default_idx])
    for i, s in enumerate(rest):
        if i == diapason_idx or i == default_idx:
            continue
        ordered.append(s)
    return ' '.join(ordered)


def split_ompr(ompr: str) -> tuple[str, str]:
    if not ompr:
        return '', ''
    parts = [p.strip() for p in ompr.split('/', maxsplit=1)]
    if len(parts) == 2:
        return parts[0], parts[1]
    elif len(parts) == 1:
        return parts[0], ''
    else:
        return '', ''


def transform_row(row: dict[str, str]) -> dict[str, str]:
    param = row.get('Параметр', '')
    ompr = row.get('OMPR', '')
    desc = row.get('Описание', '')

    type_val = extract_type(desc) or ''
    desc_wo_type = remove_type_sentence(desc)
    om, pr = split_ompr(ompr)
    desc_reordered = reorder_description(desc_wo_type)

    return {
        'Параметр': param,
        'Описание': desc_reordered.strip(),
        'Тип': type_val,
        'O/M': om,
        'P/R': pr
    }


def transform_table(text: str) -> list[dict[str, str]]:
    rows = read_table(text)
    return [transform_row(row) for row in rows]


def to_markdown(rows: list[dict[str, str]]) -> str:
    headers = ['Параметр', 'Описание', 'Тип', 'O/M', 'P/R']
    out = ['| ' + ' | '.join(headers) + ' |', '|' + '|'.join(['---'] * len(headers)) + '|']
    for row in rows:
        out.append('| ' + ' | '.join(row.get(h, '') for h in headers) + ' |')
    return '\n'.join(out)


def to_asciidoc(rows: list[dict[str, str]]) -> str:
    headers = ['Параметр', 'Описание', 'Тип', 'O/M', 'P/R']
    out = ['|===', '| ' + ' | '.join(headers)]
    for row in rows:
        out.append('| ' + ' | '.join(row.get(h, '') for h in headers))
    out.append('|===')
    return '\n'.join(out)


def process_tables_in_text(text: str, input_format: str = "markdown", output_format: Optional[str] = None) -> str:
    """
    Finds all tables in the text, transforms them, and returns the text with tables replaced by their transformed
    versions.
    """
    tables = find_tables(text)
    transformed_tables = []
    for table in tables:
        rows = transform_table(table)
        fmt = output_format or input_format
        if fmt == "markdown":
            transformed = to_markdown(rows)
        elif fmt == "asciidoc":
            transformed = to_asciidoc(rows)
        else:
            raise ValueError("Unknown output format: " + fmt)
        transformed_tables.append((table, transformed))

    # Replace each original table with its transformed version in the text
    new_text = text
    for original, transformed in transformed_tables:
        new_text = new_text.replace(original, transformed)
        print("Transformed table:\n", transformed)

    return new_text


if __name__ == '__main__':
    with open(
            "/Users/andrewtarasov/PycharmProjects/SB/content/common/config/congestion.cfg.md",
            "r",
            encoding="utf-8",
            errors="ignore") as f:
        text: str = f.read()

    result: str = process_tables_in_text(text, "markdown", "markdown")
    print(result)
