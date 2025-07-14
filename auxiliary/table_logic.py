# -*- coding: utf-8 -*-
import re
from typing import List, Dict, Optional, Union, Iterator
from abc import ABC, abstractmethod


class Cell:
    """Represents a single table cell."""

    def __init__(self, value: str = "", row_index: int = 0, column_index: int = 0):
        self._value = value
        self._row_index = row_index
        self._column_index = column_index
        self._original_value = value

    @property
    def value(self) -> str:
        """Get cell value."""
        return self._value

    @value.setter
    def value(self, new_value: str) -> None:
        """Set cell value."""
        self._value = str(new_value) if new_value is not None else ""

    @property
    def row_index(self) -> int:
        """Get row index."""
        return self._row_index

    @property
    def column_index(self) -> int:
        """Get column index."""
        return self._column_index

    @property
    def original_value(self) -> str:
        """Get original cell value."""
        return self._original_value

    def is_empty(self) -> bool:
        """Check if cell is empty."""
        return len(self._value.strip()) == 0

    def clear(self) -> None:
        """Clear cell value."""
        self._value = ""

    def restore(self) -> None:
        """Restore cell to original value."""
        self._value = self._original_value

    def contains(self, text: str) -> bool:
        """Check if cell contains specific text."""
        return text in self._value

    def matches_regex(self, pattern: str) -> bool:
        """Check if cell matches regex pattern."""
        return bool(re.search(pattern, self._value))

    def apply_regex(self, pattern: str, replacement: str = "") -> str:
        """Apply regex replacement and return result."""
        return re.sub(pattern, replacement, self._value)

    def extract_regex(self, pattern: str) -> Optional[str]:
        """Extract text using regex pattern."""
        match = re.search(pattern, self._value)
        return match.group(1) if match else None

    def _update_indices(self, row_index: int, column_index: int) -> None:
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


class Column:
    """Represents a table column."""

    def __init__(self, name: str, index: int = 0):
        self._name = name
        self._index = index
        self._cells: List[Cell] = []
        self._original_name = name

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

    @property
    def original_name(self) -> str:
        """Get original column name."""
        return self._original_name

    @property
    def cells(self) -> List[Cell]:
        """Get all cells in column."""
        return self._cells.copy()

    def add_cell(self, cell: Cell) -> None:
        """Add a cell to the column."""
        cell._update_indices(len(self._cells), self._index)
        self._cells.append(cell)

    def insert_cell(self, index: int, cell: Cell) -> None:
        """Insert a cell at specific index."""
        cell._update_indices(index, self._index)
        self._cells.insert(index, cell)
        # Update indices for cells after insertion
        for i in range(index + 1, len(self._cells)):
            self._cells[i]._update_indices(i, self._index)

    def remove_cell(self, index: int) -> Cell:
        """Remove cell at specific index."""
        if 0 <= index < len(self._cells):
            cell = self._cells.pop(index)
            # Update indices for remaining cells
            for i in range(index, len(self._cells)):
                self._cells[i]._update_indices(i, self._index)
            return cell
        raise IndexError(f"Cell index {index} out of range")

    def get_cell(self, index: int) -> Cell:
        """Get cell at specific index."""
        if 0 <= index < len(self._cells):
            return self._cells[index]
        raise IndexError(f"Cell index {index} out of range")

    def set_cell_value(self, index: int, value: str) -> None:
        """Set value of cell at specific index."""
        if 0 <= index < len(self._cells):
            self._cells[index].value = value
        else:
            raise IndexError(f"Cell index {index} out of range")

    def get_cell_value(self, index: int) -> str:
        """Get value of cell at specific index."""
        if 0 <= index < len(self._cells):
            return self._cells[index].value
        raise IndexError(f"Cell index {index} out of range")

    def get_values(self) -> List[str]:
        """Get all cell values as list."""
        return [cell.value for cell in self._cells]

    def set_values(self, values: List[str]) -> None:
        """Set all cell values."""
        for i, value in enumerate(values):
            if i < len(self._cells):
                self._cells[i].value = value
            else:
                cell = Cell(value, i, self._index)
                self._cells.append(cell)

    def find_cells_containing(self, text: str) -> List[int]:
        """Find indices of cells containing specific text."""
        return [i for i, cell in enumerate(self._cells) if cell.contains(text)]

    def find_cells_matching_regex(self, pattern: str) -> List[int]:
        """Find indices of cells matching regex pattern."""
        return [i for i, cell in enumerate(self._cells) if cell.matches_regex(pattern)]

    def apply_regex_to_all(self, pattern: str, replacement: str = "") -> None:
        """Apply regex replacement to all cells."""
        for cell in self._cells:
            cell.value = cell.apply_regex(pattern, replacement)

    def size(self) -> int:
        """Get number of cells in column."""
        return len(self._cells)

    def is_empty(self) -> bool:
        """Check if all cells in column are empty."""
        return all(cell.is_empty() for cell in self._cells)

    def clear_all(self) -> None:
        """Clear all cells in column."""
        for cell in self._cells:
            cell.clear()

    def _update_index(self, new_index: int) -> None:
        """Update column index (internal method)."""
        self._index = new_index
        for cell in self._cells:
            cell._update_indices(cell.row_index, new_index)

    def __len__(self) -> int:
        return len(self._cells)

    def __getitem__(self, index: int) -> Cell:
        return self.get_cell(index)

    def __setitem__(self, index: int, value: Union[str, Cell]) -> None:
        if isinstance(value, Cell):
            value._update_indices(index, self._index)
            self._cells[index] = value
        else:
            self.set_cell_value(index, str(value))

    def __iter__(self) -> Iterator[Cell]:
        return iter(self._cells)

    def __str__(self) -> str:
        return f"Column({self._name})"

    def __repr__(self) -> str:
        return f"Column(name='{self._name}', index={self._index}, cells={len(self._cells)})"


class Row:
    """Represents a table row."""

    def __init__(self, index: int = 0):
        self._index = index
        self._cells: List[Cell] = []

    @property
    def index(self) -> int:
        """Get row index."""
        return self._index

    @property
    def cells(self) -> List[Cell]:
        """Get all cells in row."""
        return self._cells.copy()

    def add_cell(self, cell: Cell) -> None:
        """Add a cell to the row."""
        cell._update_indices(self._index, len(self._cells))
        self._cells.append(cell)

    def insert_cell(self, index: int, cell: Cell) -> None:
        """Insert a cell at specific index."""
        cell._update_indices(self._index, index)
        self._cells.insert(index, cell)
        # Update indices for cells after insertion
        for i in range(index + 1, len(self._cells)):
            self._cells[i]._update_indices(self._index, i)

    def remove_cell(self, index: int) -> Cell:
        """Remove cell at specific index."""
        if 0 <= index < len(self._cells):
            cell = self._cells.pop(index)
            # Update indices for remaining cells
            for i in range(index, len(self._cells)):
                self._cells[i]._update_indices(self._index, i)
            return cell
        raise IndexError(f"Cell index {index} out of range")

    def get_cell(self, index: int) -> Cell:
        """Get cell at specific index."""
        if 0 <= index < len(self._cells):
            return self._cells[index]
        raise IndexError(f"Cell index {index} out of range")

    def set_cell_value(self, index: int, value: str) -> None:
        """Set value of cell at specific index."""
        if 0 <= index < len(self._cells):
            self._cells[index].value = value
        else:
            raise IndexError(f"Cell index {index} out of range")

    def get_cell_value(self, index: int) -> str:
        """Get value of cell at specific index."""
        if 0 <= index < len(self._cells):
            return self._cells[index].value
        raise IndexError(f"Cell index {index} out of range")

    def get_values(self) -> List[str]:
        """Get all cell values as list."""
        return [cell.value for cell in self._cells]

    def set_values(self, values: List[str]) -> None:
        """Set all cell values."""
        # Clear existing cells
        self._cells.clear()
        # Add new cells
        for i, value in enumerate(values):
            cell = Cell(value, self._index, i)
            self._cells.append(cell)

    def find_cells_containing(self, text: str) -> List[int]:
        """Find indices of cells containing specific text."""
        return [i for i, cell in enumerate(self._cells) if cell.contains(text)]

    def find_cells_matching_regex(self, pattern: str) -> List[int]:
        """Find indices of cells matching regex pattern."""
        return [i for i, cell in enumerate(self._cells) if cell.matches_regex(pattern)]

    def apply_regex_to_all(self, pattern: str, replacement: str = "") -> None:
        """Apply regex replacement to all cells."""
        for cell in self._cells:
            cell.value = cell.apply_regex(pattern, replacement)

    def size(self) -> int:
        """Get number of cells in row."""
        return len(self._cells)

    def is_empty(self) -> bool:
        """Check if all cells in row are empty."""
        return all(cell.is_empty() for cell in self._cells)

    def clear_all(self) -> None:
        """Clear all cells in row."""
        for cell in self._cells:
            cell.clear()

    def extend_to_size(self, size: int) -> None:
        """Extend row to specified size with empty cells."""
        while len(self._cells) < size:
            cell = Cell("", self._index, len(self._cells))
            self._cells.append(cell)

    def _update_index(self, new_index: int) -> None:
        """Update row index (internal method)."""
        self._index = new_index
        for cell in self._cells:
            cell._update_indices(new_index, cell.column_index)

    def __len__(self) -> int:
        return len(self._cells)

    def __getitem__(self, index: int) -> Cell:
        return self.get_cell(index)

    def __setitem__(self, index: int, value: Union[str, Cell]) -> None:
        if isinstance(value, Cell):
            value._update_indices(self._index, index)
            self._cells[index] = value
        else:
            self.set_cell_value(index, str(value))

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
            table.add_column(column)

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
                    row.add_cell(cell)
                    if col_idx < len(table.columns):
                        table.get_column(col_idx).add_cell(cell)

                table.add_row(row)

        return table

    def serialize(self, table: 'Table') -> str:
        """Convert table to Markdown format."""
        if table.column_count == 0:
            return ""

        # Create header row
        header_names = [col.name for col in table.columns]
        header_row = '| ' + ' | '.join(header_names) + ' |'

        # Create separator row
        separator_row = '| ' + ' | '.join(['---'] * table.column_count) + ' |'

        # Create data rows
        data_rows = []
        for row in table.rows:
            values = []
            for i in range(table.column_count):
                if i < len(row.cells):
                    values.append(row.cells[i].value)
                else:
                    values.append('')
            row_str = '| ' + ' | '.join(values) + ' |'
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
                        table.add_column(column)
                    header_parsed = True
                else:
                    # Data row
                    row = Row(row_idx)

                    # Ensure row has same number of cells as columns
                    while len(cell_values) < table.column_count:
                        cell_values.append('')

                    for col_idx, value in enumerate(cell_values):
                        cell = Cell(value, row_idx, col_idx)
                        row.add_cell(cell)
                        if col_idx < table.column_count:
                            table.get_column(col_idx).add_cell(cell)

                    table.add_row(row)
                    row_idx += 1

        return table

    def serialize(self, table: 'Table') -> str:
        """Convert table to AsciiDoc format."""
        if table.column_count == 0:
            return "|===\n|==="

        # Build table content
        table_lines = []
        table_lines.append('|===')

        # Add header
        header_names = [col.name for col in table.columns]
        header_row = '| ' + ' | '.join(header_names)
        table_lines.append(header_row)

        # Add data rows
        for row in table.rows:
            values = []
            for i in range(table.column_count):
                if i < len(row.cells):
                    values.append(row.cells[i].value)
                else:
                    values.append('')
            row_str = '| ' + ' | '.join(values)
            table_lines.append(row_str)

        table_lines.append('|===')

        return '\n'.join(table_lines)


class TableParserFactory:
    """Factory class for creating table parsers."""

    @staticmethod
    def create_parser(format_type: str) -> TableParser:
        """Create appropriate parser based on format type."""
        if format_type == 'markdown':
            return MarkdownTableParser()
        elif format_type == 'asciidoc':
            return AsciiDocTableParser()
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    @staticmethod
    def detect_format(content: str) -> str:
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
    """Represents a complete table with rows and columns."""

    def __init__(self):
        self._columns: List[Column] = []
        self._rows: List[Row] = []
        self._format = 'markdown'
        self._parser: Optional[TableParser] = None

    @property
    def columns(self) -> List[Column]:
        """Get all columns."""
        return self._columns.copy()

    @property
    def rows(self) -> List[Row]:
        """Get all rows."""
        return self._rows.copy()

    @property
    def column_count(self) -> int:
        """Get number of columns."""
        return len(self._columns)

    @property
    def row_count(self) -> int:
        """Get number of rows."""
        return len(self._rows)

    @property
    def format(self) -> str:
        """Get table format."""
        return self._format

    def set_format(self, format_type: str) -> None:
        """Set table format."""
        self._format = format_type
        self._parser = TableParserFactory.create_parser(format_type)

    def add_column(self, column: Column) -> None:
        """Add a column to the table."""
        column._update_index(len(self._columns))
        self._columns.append(column)

    def insert_column(self, index: int, column: Column) -> None:
        """Insert a column at specific index."""
        column._update_index(index)
        self._columns.insert(index, column)
        # Update indices for columns after insertion
        for i in range(index + 1, len(self._columns)):
            self._columns[i]._update_index(i)
        # Update cell column indices in all rows
        for row in self._rows:
            for cell in row.cells:
                if cell.column_index >= index:
                    cell._update_indices(cell.row_index, cell.column_index + 1)

    def remove_column(self, index: int) -> Column:
        """Remove column at specific index."""
        if 0 <= index < len(self._columns):
            column = self._columns.pop(index)
            # Update indices for remaining columns
            for i in range(index, len(self._columns)):
                self._columns[i]._update_index(i)
            # Remove cells from rows and update indices
            for row in self._rows:
                if index < len(row.cells):
                    row.remove_cell(index)
            return column
        raise IndexError(f"Column index {index} out of range")

    def get_column(self, index: int) -> Column:
        """Get column at specific index."""
        if 0 <= index < len(self._columns):
            return self._columns[index]
        raise IndexError(f"Column index {index} out of range")

    def get_column_by_name(self, name: str) -> Optional[Column]:
        """Get column by name."""
        for column in self._columns:
            if column.name == name:
                return column
        return None

    def find_column_index(self, name: str) -> int:
        """Find column index by name."""
        for i, column in enumerate(self._columns):
            if column.name == name:
                return i
        return -1

    def add_row(self, row: Row) -> None:
        """Add a row to the table."""
        row._update_index(len(self._rows))
        # Extend row to match column count
        row.extend_to_size(self.column_count)
        self._rows.append(row)

    def insert_row(self, index: int, row: Row) -> None:
        """Insert a row at specific index."""
        row._update_index(index)
        row.extend_to_size(self.column_count)
        self._rows.insert(index, row)
        # Update indices for rows after insertion
        for i in range(index + 1, len(self._rows)):
            self._rows[i]._update_index(i)

    def remove_row(self, index: int) -> Row:
        """Remove row at specific index."""
        if 0 <= index < len(self._rows):
            row = self._rows.pop(index)
            # Update indices for remaining rows
            for i in range(index, len(self._rows)):
                self._rows[i]._update_index(i)
            # Remove cells from columns
            for column in self._columns:
                if index < len(column.cells):
                    column.remove_cell(index)
            return row
        raise IndexError(f"Row index {index} out of range")

    def get_row(self, index: int) -> Row:
        """Get row at specific index."""
        if 0 <= index < len(self._rows):
            return self._rows[index]
        raise IndexError(f"Row index {index} out of range")

    def get_cell(self, row_index: int, column_index: int) -> Cell:
        """Get cell at specific coordinates."""
        if 0 <= row_index < len(self._rows) and 0 <= column_index < len(self._columns):
            return self._rows[row_index].get_cell(column_index)
        raise IndexError(f"Cell coordinates ({row_index}, {column_index}) out of range")

    def set_cell_value(self, row_index: int, column_index: int, value: str) -> None:
        """Set cell value at specific coordinates."""
        cell = self.get_cell(row_index, column_index)
        cell.value = value

    def get_cell_value(self, row_index: int, column_index: int) -> str:
        """Get cell value at specific coordinates."""
        cell = self.get_cell(row_index, column_index)
        return cell.value

    def add_empty_column(self, name: str, index: Optional[int] = None) -> Column:
        """Add an empty column."""
        column = Column(name)
        # Add empty cells for existing rows
        for row_idx in range(len(self._rows)):
            cell = Cell("", row_idx, column.index)
            column.add_cell(cell)

        if index is None:
            self.add_column(column)
        else:
            self.insert_column(index, column)
            # Insert empty cells in existing rows
            for row_idx, row in enumerate(self._rows):
                cell = Cell("", row_idx, index)
                row.insert_cell(index, cell)

        return column

    def reorder_columns(self, column_order: List[str]) -> None:
        """Reorder columns according to specified order."""
        # Create new column list in specified order
        new_columns = []
        old_indices = []

        for name in column_order:
            for i, column in enumerate(self._columns):
                if column.name == name:
                    new_columns.append(column)
                    old_indices.append(i)
                    break

        # Add any columns not in the specified order
        for i, column in enumerate(self._columns):
            if i not in old_indices:
                new_columns.append(column)
                old_indices.append(i)

        # Update column indices
        for i, column in enumerate(new_columns):
            column.update_index(i)

        # Reorder cells in rows
        for row in self._rows:
            new_cells = []
            for old_idx in old_indices:
                if old_idx < len(row.cells):
                    cell = row.cells[old_idx]
                    cell._update_indices(row.index, len(new_cells))
                    new_cells.append(cell)
                else:
                    cell = Cell("", row.index, len(new_cells))
                    new_cells.append(cell)
            row._cells = new_cells

        self._columns = new_columns

    def split_column(self, column_name: str, new_names: List[str],
                     split_function: callable) -> List[Column]:
        """Split a column into multiple columns using a custom function."""
        column_index = self.find_column_index(column_name)
        if column_index == -1:
            return []

        # Remove original column
        original_column = self.remove_column(column_index)

        # Create new columns
        new_columns = []
        for i, name in enumerate(new_names):
            new_column = Column(name, column_index + i)
            new_columns.append(new_column)
            self.insert_column(column_index + i, new_column)

        # Split data in each row
        for row_idx, row in enumerate(self._rows):
            if column_index < len(row.cells):
                original_value = row.cells[column_index].value
                split_values = split_function(original_value)

                # Ensure we have enough values
                while len(split_values) < len(new_names):
                    split_values.append("")

                # Set values in new columns
                for i, value in enumerate(split_values):
                    if i < len(new_names):
                        self.set_cell_value(row_idx, column_index + i, value)

        return new_columns

    def split_ompr_column(self) -> List[Column]:
        """Split OMPR/OMXPR column to O/M and P/R columns."""

        def split_function(value: str) -> List[str]:
            match = re.match(r'([OM])([PR])', value)
            if match:
                return [match.group(1), match.group(2)]
            return ["", ""]

        # Try both possible column names
        for name in ['OMPR', 'OMXPR']:
            if self.find_column_index(name) != -1:
                return self.split_column(name, ['O/M', 'P/R'], split_function)
        return []

    def split_description_column(self) -> List[Column]:
        """Split Описание column to Описание and Тип columns."""

        def split_function(value: str) -> List[str]:
            type_match = re.search(r'Тип -- (.*?)(?:\n|$)', value)
            if type_match:
                type_value = type_match.group(1).strip()
                new_desc = re.sub(r'Тип -- .*?(?:\n|$)', '', value).strip()
                return [new_desc, type_value]
            return [value, ""]

        return self.split_column('Описание')