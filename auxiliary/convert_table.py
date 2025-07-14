# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
import re
from typing import Iterable, Iterator, Literal

from common.functions import file_reader
from common.shared import StrPath

FormatType: type[str] = Literal["markdown", "asciidoc"]


def bound(text: Iterable[str], *, prefix: str = "", suffix: str = ""):
    line: str = " | ".join(text)

    return f"{prefix}{line}{suffix}"


class Cell:
    """Represents a single table cell."""

    def __init__(self, value: str = "", row_index: int = 0, column_index: int = 0):
        self._value = value
        self._row_index = row_index
        self._column_index = column_index

    def update_indices(self, row_index: int, column_index: int) -> None:
        """Update cell indices (internal method)."""
        self._row_index = row_index
        self._column_index = column_index

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"Cell(value='{self._value}', row={self._row_index}, col={self._column_index})"

    def __eq__(self, other) -> bool:
        if isinstance(other, Cell):
            return self._value == other._value
        return self._value == str(other)

    @property
    def row_index(self):
        return self._row_index

    @property
    def column_index(self):
        return self._column_index

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


class Column:
    """Represents a table column."""

    def __init__(self, name: str, index: int = 0):
        self._name = name
        self._index = index
        self._cells: list[Cell] = []

    def __add__(self, other):
        if isinstance(other, Cell):
            other.update_indices(len(self) + 1, self._index)
            self._cells.append(other)

    @property
    def name(self) -> str:
        """Get column name."""
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        """Set column name."""
        self._name = str(new_name)

    @property
    def index(self) -> int:
        """Get column index."""
        return self._index

    def update_index(self, new_index: int) -> None:
        """Update column index (internal method)."""
        self._index = new_index
        for cell in self._cells:
            cell.update_indices(cell.row_index, new_index)

    def __len__(self) -> int:
        return len(self._cells)

    def __getitem__(self, key: int) -> Cell:
        return self._cells[key]

    def __setitem__(self, index: int, value: str | Cell) -> None:
        if isinstance(value, Cell):
            value.update_indices(index, self._index)
            self._cells[index] = value

        elif 0 <= index < len(self._cells):
            self._cells[index].value = value

        else:
            raise IndexError(f"Cell index {index} out of range")

    def __iter__(self) -> Iterator[Cell]:
        return iter(self._cells)

    def __str__(self) -> str:
        return f"Column({self._name})"

    def __repr__(self) -> str:
        return f"Column(name='{self._name}', index={self._index}, cells={len(self._cells)})"

    @property
    def cells(self):
        return self._cells


class Row:
    """Represents a table row."""

    def __init__(self, index: int = 0):
        self._index = index
        self._cells: list[Cell] = []

    def __add__(self, other):
        if isinstance(other, Cell):
            other.update_indices(self._index, len(self) + 1)
            self._cells.append(other)

    @property
    def index(self) -> int:
        """Get row index."""
        return self._index

    @property
    def cells(self) -> list[Cell]:
        """Get all cells in row."""
        return self._cells.copy()

    def __getitem__(self, index: int) -> Cell:
        """Get cell at specific index."""
        if 0 <= index < len(self._cells):
            return self._cells[index]
        raise IndexError(f"Cell index {index} out of range")

    def extend_to_size(self, size: int) -> None:
        """Extend row to specified size with empty cells."""
        while len(self._cells) < size:
            cell = Cell("", self._index, len(self._cells))
            self._cells.append(cell)

    def update_index(self, new_index: int) -> None:
        """Update row index (internal method)."""
        self._index = new_index

        for cell in self._cells:
            cell.update_indices(new_index, cell.column_index)

    def __len__(self) -> int:
        return len(self._cells)

    def __setitem__(self, index: int, value: str | Cell) -> None:
        if isinstance(value, Cell):
            value.update_indices(self._index, index)
            self._cells[index] = value

        elif 0 <= index < len(self._cells):
            self._cells[index].value = value

        else:
            raise IndexError(f"Cell index {index} out of range")

    def __iter__(self) -> Iterator[Cell]:
        return iter(self._cells)

    def __str__(self) -> str:
        return f"Row({self._index}): {[cell.value for cell in self._cells]}"

    def __repr__(self) -> str:
        return f"Row(index={self._index}, cells={len(self._cells)})"


class TableParser(ABC):
    """Abstract base class for table parsers."""

    @abstractmethod
    def parse(self, content: str) -> 'Table':
        """Parse table content and return Table object."""
        pass

    @abstractmethod
    def serialize(self, table: 'Table') -> str:
        """Serialize table object back to string format."""
        pass


class MarkdownTableParser(TableParser):
    """Parser for Markdown tables."""

    def parse(self, content: str) -> 'Table':
        """Parse a Markdown table."""
        lines = content.strip().split('\n')

        # Find table boundaries
        table_lines = []
        for line in lines:
            if '|' in line:
                table_lines.append(line.strip())

        if len(table_lines) < 2:
            raise ValueError("Invalid Markdown table format")

        # Parse header
        header_line = table_lines[0]
        header_names = [cell.strip() for cell in header_line.split('|')[1:-1]]

        # Create table
        table = Table()

        # Add columns
        for i, name in enumerate(header_names):
            column = Column(name, i)
            table + column

        # Parse data rows
        for row_idx, line in enumerate(table_lines[2:]):  # Skip separator line
            if line.strip():
                row = Row(row_idx)
                cell_values = [cell.strip() for cell in line.split('|')[1:-1]]

                # Ensure row has same number of cells as columns
                while len(cell_values) < len(header_names):
                    cell_values.append('')

                for col_idx, value in enumerate(cell_values):
                    cell = Cell(value, row_idx, col_idx)
                    row + cell
                    if col_idx < len(table.columns):
                        table.get_column(col_idx) + cell

                table + row

        return table

    def serialize(self, table: 'Table') -> str:
        """Convert table to Markdown format."""
        if not table.column_count:
            return ""

        # Create header row
        header_names = [col.name for col in table.columns]
        header_row = bound(header_names, prefix="| ", suffix=" |")

        # Create separator row
        separator_str = ' | '.join(['---'] * table.column_count)
        separator_row = f'| {separator_str} |'

        # Create data rows
        data_rows = []

        for row in table.rows:
            values = []
            for i in range(table.column_count):
                if i < len(row.cells):
                    values.append(row.cells[i].value)
                else:
                    values.append('')
            row_str = bound(values, prefix="| ", suffix=" |")
            data_rows.append(row_str)

        return '\n'.join([header_row, separator_row] + data_rows)


class AsciiDocTableParser(TableParser):
    """Parser for AsciiDoc tables."""

    def parse(self, content: str) -> 'Table':
        """Parse an AsciiDoc table."""
        lines = content.strip().split('\n')

        # Find table start and end
        table_start = -1
        table_end = -1

        for i, line in enumerate(lines):
            if '|===' in line and table_start == -1:
                table_start = i
            elif '|===' in line and table_start != -1:
                table_end = i
                break

        if table_start == -1 or table_end == -1:
            raise ValueError("Invalid AsciiDoc table format")

        # Parse table content
        table_lines = lines[table_start + 1:table_end]

        # Create table
        table = Table()

        # Parse header and data
        header_parsed = False
        row_idx = 0

        for line in table_lines:
            if line.strip():
                cell_values = [cell.strip() for cell in line.split('|')[1:]]

                if not header_parsed:
                    # First row is header
                    for i, name in enumerate(cell_values):
                        column = Column(name, i)
                        table + column
                    header_parsed = True
                else:
                    # Data row
                    row = Row(row_idx)

                    # Ensure row has same number of cells as columns
                    while len(cell_values) < table.column_count:
                        cell_values.append('')

                    for col_idx, value in enumerate(cell_values):
                        cell = Cell(value, row_idx, col_idx)
                        row + cell
                        if col_idx < table.column_count:
                            table.get_column(col_idx) + cell

                    table + row
                    row_idx += 1

        return table

    def serialize(self, table: 'Table') -> str:
        """Convert table to AsciiDoc format."""
        if not table.column_count:
            return "|===\n|==="

        # Build table content
        table_lines = ['|===']

        # Add header
        header_names = [col.name for col in table.columns]
        header_row = bound(header_names, prefix="|")
        table_lines.append(header_row)

        # Add data rows
        for row in table.rows:
            values = []
            for i in range(table.column_count):
                if i < len(row.cells):
                    values.append(row.cells[i].value)
                else:
                    values.append('')
            row_str = bound(values, prefix="|")
            table_lines.append(row_str)

        table_lines.append('|===')

        return '\n'.join(table_lines)


def create_parser(format_type: str) -> TableParser:
    """Create appropriate parser based on format type."""
    if format_type == 'markdown':
        return MarkdownTableParser()
    elif format_type == 'asciidoc':
        return AsciiDocTableParser()
    else:
        raise ValueError(f"Unsupported format: {format_type}")


def detect_format(content: str) -> FormatType:
    """Detect table format from content."""
    # Check for Markdown table indicators
    if '|' in content and '---' in content:
        return 'markdown'
    # Check for AsciiDoc table indicators
    elif '|===' in content or '[cols=' in content:
        return 'asciidoc'
    else:
        # Default to markdown if unclear
        return 'markdown'


class Table:
    """Represents a complete table composed of cells."""

    def __init__(self, cells: Iterable[Cell] = None):
        if cells is None:
            cells: list[Cell] = []

        else:
            cells: list[Cell] = [*cells]

        self._format = 'markdown'
        self._parser: TableParser | None = None
        self._cells = cells

    @property
    def column_count(self) -> int:
        return len(self.columns)

    def set_format(self, format_type: str) -> None:
        self._format = format_type
        self._parser = create_parser(format_type)

    @property
    def columns(self) -> list[Column]:
        column_map: dict[int, Column] = {}
        for cell in self._cells:
            col = column_map.setdefault(
                cell.column_index,
                Column(name=f"Col{cell.column_index}", index=cell.column_index)
            )
            col + cell
        return [column_map[i] for i in sorted(column_map)]

    @property
    def rows(self) -> list[Row]:
        row_map: dict[int, Row] = {}
        for cell in self._cells:
            row = row_map.setdefault(cell.row_index, Row(index=cell.row_index))
            row[cell.column_index] = cell
        return [row_map[i] for i in sorted(row_map)]

    def get_cell(self, row_index: int, column_index: int) -> Cell:
        for cell in self._cells:
            if cell.row_index == row_index and cell.column_index == column_index:
                return cell
        raise IndexError(f"Cell coordinates ({row_index}, {column_index}) out of range")

    def get_column(self, index: int) -> Column:
        try:
            return self.columns[index]
        except IndexError:
            raise IndexError(f"Column index {index} out of range")

    def get_column_by_name(self, name: str) -> Column | None:
        return next((col for col in self.columns if col.name == name), None)

    def find_column_index(self, name: str) -> int:
        for i, col in enumerate(self.columns):
            if col.name == name:
                return i
        return -1

    def get_row(self, index: int) -> Row:
        try:
            return self.rows[index]
        except IndexError:
            raise IndexError(f"Row index {index} out of range")

    def insert_column(self, index: int, column: Column) -> None:
        column.update_index(index)
        for cell in column.cells:
            self._cells.append(cell)
        for cell in self._cells:
            if cell.column_index >= index:
                cell.update_indices(cell.row_index, cell.column_index + 1)

    def __add__(self, other):
        if isinstance(other, Row):
            other.update_index(len(self.rows))
            other.extend_to_size(self.column_count)
            self._cells.extend(other.cells)
        elif isinstance(other, Column):
            self.insert_column(len(self.columns), other)
        return self

    def add_empty_column(self, name: str, index: int | None = None) -> Column:
        column = Column(name)
        for row_idx in range(len(self.rows)):
            column + Cell("", row_idx, column.index)
        if index is None:
            self + column
        else:
            self.insert_column(index, column)
            for row_idx in range(len(self.rows)):
                self._cells.append(Cell("", row_idx, index))
        return column

    def reorder_columns(self, column_order: list[str]) -> None:
        new_order = [self.get_column_by_name(name) for name in column_order if self.get_column_by_name(name)]
        others = [col for col in self.columns if col not in new_order]
        new_columns = new_order + others
        index_map = {col.index: i for i, col in enumerate(new_columns)}

        for cell in self._cells:
            cell.update_indices(cell.row_index, index_map.get(cell.column_index, cell.column_index))

    def split_column(self, column_name: str, new_names: list[str], split_function: callable) -> list[Column]:
        column_index = self.find_column_index(column_name)
        if column_index == -1:
            return []

        new_columns = [Column(name, column_index + i) for i, name in enumerate(new_names)]
        for col in reversed(new_columns):
            self.insert_column(col.index, col)

        for row_idx, row in enumerate(self.rows):
            if column_index < len(row.cells):
                values = split_function(row.cells[column_index].value)
                values.extend([""] * (len(new_names) - len(values)))
                for i, value in enumerate(values):
                    self.get_cell(row_idx, column_index + i).value = value
        return new_columns

    def split_ompr_column(self) -> list[Column]:
        def split_fn(val: str) -> list[str]:
            m = re.match(r'([OM])([PR])', val)
            return [m.group(1), m.group(2)] if m else ["", ""]

        for name in ['OMPR', 'OMXPR']:
            if self.find_column_index(name) != -1:
                return self.split_column(name, ['O/M', 'P/R'], split_fn)
        return []

    def split_description_column(self) -> list[Column]:
        def split_fn(val: str) -> list[str]:
            match = re.search(r'Tип -- (.*?)(?:\n|$)', val)
            if match:
                t = match.group(1).strip()
                desc = re.sub(r'Tип -- .*?(?:\n|$)\.?', '', val).strip()
                return [desc, t]
            return [val, ""]

        return self.split_column('Описание', ['Описание', 'Тип'], split_fn)


def extract_tables_from_text(file: StrPath) -> list[Table]:
    """
    Extract tables from Markdown or AsciiDoc formatted text.

    Args:
        file (str): The full text content to scan.

    Returns:
        list[Table]: List of parsed Table objects.
    """
    tables: list[Table] = []

    patterns: dict[FormatType, re.Pattern] = {
        "markdown": re.compile(r"(?:^\|.*\|.*$\n)+", re.MULTILINE),
        "asciidoc": re.compile(r"|===\n.*?\n\|===", re.MULTILINE | re.DOTALL)}

    text: str = file_reader(file, "string")
    format_type: FormatType = detect_format(text)

    for block in patterns.get(format_type).findall(text):
        table_parser: TableParser = create_parser(format_type)
        table: Table = table_parser.parse(block)
        tables.append(table)

    return tables
