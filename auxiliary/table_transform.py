# -*- coding: utf-8 -*-
from pathlib import Path
from re import compile, Match, match, Pattern
from typing import Iterable, NamedTuple, Sequence

from loguru import logger

from utilities.common.functions import file_reader, file_writer, pretty_print
from utilities.common.shared import StrPath


class TableCoordinate(NamedTuple):
    row: int
    col: int

    def __str__(self) -> str:
        return f"{self.row}, {self.col}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(row={self.row}, col={self.col})"


class TableCell:
    def __init__(self, content: str, table_coordinate: TableCoordinate = None) -> None:
        self._content: str = content
        self._table_coordinate: TableCoordinate | None = table_coordinate

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        self._content = value

    @property
    def table_coordinate(self) -> TableCoordinate | None:
        return self._table_coordinate

    @table_coordinate.setter
    def table_coordinate(self, coord: TableCoordinate) -> None:
        self._table_coordinate = coord

    def __str__(self) -> str:
        return self._content

    def __repr__(self) -> str:
        return f"TableCell(content={self._content!r}, coord={self._table_coordinate})"

    def as_tuple(self):
        return self._content, self._table_coordinate

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TableCell):
            return self.as_tuple() == other.as_tuple()
        else:
            return NotImplemented

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash((self._content, self._table_coordinate))


class TableRow:
    def __init__(self, cells: Iterable[TableCell] = None) -> None:
        if cells is None:
            cells: list[TableCell] = []
        else:
            cells: list[TableCell] = [*cells]
        self._cells: list[TableCell] = cells

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

    def __str__(self) -> str:
        return " | ".join(str(cell) for cell in self._cells)

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


class TableColumn:
    def __init__(self, cells: Iterable[TableCell] = None) -> None:
        if cells is None:
            cells: list[TableCell] = []

        else:
            cells: list[TableCell] = [*cells]

        self._cells: list[TableCell] = cells

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

    def __str__(self) -> str:
        return ".".join(str(cell) for cell in self._cells)

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


def extract_match_from_text(text: str, pattern: Pattern) -> tuple[str, str]:
    """Extract matched group and return cleaned text and extracted string or empty string."""
    m: Match = pattern.search(text)

    if m:
        extracted: str = str(m.group(1).strip())
        cleaned: str = pattern.sub("", text).strip()
        return cleaned, extracted
    else:
        return text, ""


def split_cell_content(content: str) -> tuple[str, str]:
    """Split 'X / Y' pattern, returns tuple (X, Y) or ('', '') if no match."""
    # Handle both "O/R" and "O /R" patterns
    m: Match = match(r"\s*(.*?)\s*/\s*(.*?)\s*$", content.strip())

    if m:
        return str(m.group(1).strip()), str(m.group(2).strip())

    else:
        return "", ""


class Table:
    def __init__(
            self,
            start: int,
            stop: int,
            rows: Iterable[TableRow] = None,
            lines: Iterable[str] = None) -> None:
        if rows is None:
            rows: list[TableRow] = []

        else:
            rows: list[TableRow] = [*rows]

        if lines is None:
            lines: list[str] = []

        else:
            lines: list[str] = [*lines]

        self._rows: list[TableRow] = rows
        self._lines: list[str] = lines

        self.start: int = start
        self.stop: int = stop

    def normalize(self) -> None:
        max_cols: int = max(len(row) for row in self._rows) if self._rows else 0

        for r, row in enumerate(self._rows):
            len_row: int = len(row)

            while len_row < max_cols:
                row.insert_cell(len_row, TableCell("", TableCoordinate(r, len_row)))
                len_row += 1

            for c in range(len(row)):
                row[c].table_coordinate = TableCoordinate(r, c)

    def get_cell(self, row: int, column: int) -> TableCell:
        return self._rows[row][column]

    def get_column(self, column: int) -> TableColumn:
        return TableColumn([row[column] for row in iter(self)])

    @property
    def num_columns(self) -> int:
        return max(len(row) for row in self._rows) if self._rows else 0

    def insert_row(self, index: int, row: TableRow) -> None:
        self.normalize()
        expected_cols: int = self.num_columns

        while len(row) < expected_cols:
            row.insert_cell(len(row), TableCell(""))

        for c in range(len(row)):
            row[c].table_coordinate = TableCoordinate(index, c)

        self._rows.insert(index, row)

    def __iter__(self):
        return iter(self._rows)

    @property
    def header_row(self) -> TableRow:
        return self._rows[0]

    def insert_column(self, index: int, column: TableColumn) -> None:
        self.normalize()

        for i in range(len(self._rows)):
            cell: TableCell = column[i] if i < len(column) else TableCell("")
            cell._table_coordinate = TableCoordinate(i, index)
            self._rows[i].insert_cell(index, cell)

    def swap_rows(self, i: int, j: int) -> None:
        self._rows[i], self._rows[j] = self._rows[j], self._rows[i]
        self.normalize()

    def swap_columns(self, i: int, j: int) -> None:
        for row in self._rows:
            temp_cell = row[i]
            row.cells[i] = row[j]
            row.cells[j] = temp_cell
        self.normalize()

    def split_row(self, row_idx: int, delimiter: str = "|") -> None:
        original_row: TableRow = self._rows.pop(row_idx)
        parts_list: list[list[str]] = [cell.content.split(delimiter) for cell in original_row]
        max_parts: int = max(len(parts) for parts in parts_list)

        for i in range(max_parts):
            cells: list[TableCell] = []

            for parts in parts_list:
                content: str = parts[i].strip() if i < len(parts) else ""
                cells.append(TableCell(content))

            new_row: TableRow = TableRow(cells)
            self._rows.insert(row_idx + i, new_row)

        self.normalize()

    def split_column(self, col_idx: int, delimiter: str = "|") -> None:
        self.normalize()
        split_cells: list[list[str]] = [row[col_idx].content.split(delimiter) for row in self._rows]
        max_parts: int = max(len(parts) for parts in split_cells)

        for offset in range(max_parts):
            for row_idx, row in enumerate(self._rows):
                parts: list[str] = split_cells[row_idx]
                content: str = parts[offset].strip() if offset < len(parts) else ""
                row.insert_cell(col_idx + offset, TableCell(content))

        for row in self._rows:
            row.remove_cell(col_idx + max_parts)

        self.normalize()

    def unify_cells(self, coordinates: list[TableCoordinate]) -> None:
        if not coordinates:
            return

        contents: list[str] = [self._rows[coord.row][coord.col].content for coord in coordinates]
        unified_content: str = " ".join(contents)
        anchor: TableCoordinate = coordinates[0]
        self._rows[anchor.row][anchor.col].content = unified_content

        for coord in coordinates[1:]:
            self._rows[coord.row][coord.col].content = ""

    def fix_borders(self, fill_value: str = "") -> None:
        if not self._rows:
            return

        max_cols: int = self.num_columns

        for r, row in enumerate(self._rows):
            while len(row) < max_cols:
                row.insert_cell(len(row), TableCell(fill_value, TableCoordinate(r, len(row))))

            for column in range(len(row)):
                row[column].table_coordinate = TableCoordinate(r, column)

    def to_markdown(self) -> str:
        self.normalize()

        if not self._rows:
            return ""

        lines: list[str] = []
        header: str = "".join(("|", " | ".join(cell.content for cell in self.header_row), "|"))
        separator: str = "".join(("|", " | ".join("---" for _ in self.header_row), "|"))
        lines.append(header)
        lines.append(separator)

        for row in self._rows[1:]:
            line: str = "".join(("|", " | ".join(cell.content for cell in row), "|"))
            lines.append(line)

        lines.append("")
        return pretty_print(lines)

    @classmethod
    def from_file(cls, content: str | list[str], start: int, stop: int):
        if isinstance(content, str):
            raw_lines: list[str] = content.strip().splitlines()

        else:
            raw_lines: list[str] = content

        table_rows: list[TableRow] = []
        row_counter: int = 0

        for line in raw_lines:
            stripped_line: str = line.strip()
            # Skip empty lines and separator lines
            if not stripped_line or "---" in stripped_line:
                continue

            if stripped_line.startswith("|"):
                # Remove leading and trailing pipes, then split
                content_part = stripped_line.strip("|")
                parts: list[str] = [cell.strip() for cell in content_part.split("|")]
                cells: list[TableCell] = []

                for c, part in enumerate(parts):
                    table_coordinate: TableCoordinate = TableCoordinate(row_counter, c)
                    cells.append(TableCell(part, table_coordinate))

                table_rows.append(TableRow(cells))
                row_counter += 1

        table = cls(start, stop, rows=table_rows, lines=raw_lines)
        table.normalize()
        return table

    def __str__(self) -> str:
        return self.to_markdown()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(rows={len(self._rows)}, cols={self.num_columns})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self._rows == other._rows
        else:
            return NotImplemented

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(tuple(self._rows))

    def extract_column_values(self, col_idx: int, pattern: Pattern) -> list[str]:
        """Extracts matches from each cell in the column, cleans original cells, returns list of extracted strings."""
        extracted_values: list[str] = []

        for row in self._rows:
            if col_idx < len(row):  # Safety check
                original_text: str = row[col_idx].content
                cleaned_text, extracted = extract_match_from_text(original_text, pattern)
                row[col_idx].content = cleaned_text
                extracted_values.append(extracted)

            else:
                extracted_values.append("")  # Empty if column doesn't exist

        return extracted_values

    def insert_column_with_values(self, insert_idx: int, values: Sequence[str]):
        """Insert a new column at insert_idx with the given values."""
        self.normalize()  # Ensure table is normalized first

        cells: list[TableCell] = []

        for row_idx in range(len(self._rows)):
            if row_idx < len(values):
                cell_content: str = values[row_idx]

            else:
                cell_content: str = ""

            cells.append(TableCell(cell_content))

        column: TableColumn = TableColumn(cells)
        self.insert_column(insert_idx, column)

    def extract_type_to_new_column(self, col_idx: int):
        self.normalize()
        pattern: Pattern = compile(r"Тип\s*[-–—]{1,2}\s*([^.\s]+)(?:\s*\.|\s|$)")

        extracted_values: list[str] = self.extract_column_values(col_idx, pattern)
        extracted_values[0] = "Тип"
        self.insert_column_with_values(col_idx + 1, extracted_values)

    def split_column_ompr(self, header_name: str = "OMPR", new_headers: Sequence[str] = ("O/M", "P/R")) -> None:
        self.normalize()

        if not self._rows or not self.header_row:
            return  # empty table guard

        try:
            col_idx: int = next(i for i in range(len(self.header_row)) if self.header_row[i].content == header_name)

        except StopIteration:
            logger.warning(f"Header '{header_name}' not found in table")
            return  # header not found, do nothing

        # Extract split contents for all rows
        split_contents: list[tuple[str, str]] = []

        for row in self._rows:
            if len(row) > col_idx:
                part1, part2 = split_cell_content(row[col_idx].content)

            else:
                part1, part2 = "", ""

            split_contents.append((part1, part2))

        # Remove original column cells (including header)
        for row in self._rows:
            if len(row) > col_idx:
                row.remove_cell(col_idx)

        # Insert two new columns at col_idx with new headers and split values
        for row_idx, row in enumerate(self._rows):
            # Insert new cells for part1 and part2
            if not row_idx:  # header row
                row.insert_cell(col_idx, TableCell(new_headers[0]))
                row.insert_cell(col_idx + 1, TableCell(new_headers[1]))

            else:
                part1, part2 = split_contents[row_idx]
                row.insert_cell(col_idx, TableCell(part1))
                row.insert_cell(col_idx + 1, TableCell(part2))

        self.normalize()

    def reorder_columns_by_names(self, new_order: Sequence[str]) -> None:
        if not self._rows or not self.header_row:
            return  # Empty table guard

        current_headers: list[str] = [cell.content for cell in self.header_row]

        # Create mapping from header name to column index
        header_to_index: dict[str, int] = {header: idx for idx, header in enumerate(current_headers)}

        # Determine new column order
        new_indices: list[int] = []
        remaining_indices: set[int] = set(range(len(current_headers)))

        # Process requested headers in order
        for header in new_order:
            if header in header_to_index:
                col_idx: int = header_to_index[header]
                new_indices.append(col_idx)
                remaining_indices.discard(col_idx)

        # Add remaining columns not specified in new_order
        new_indices.extend(sorted(remaining_indices))

        # Reorder columns in each row
        for row in self._rows:
            original_cells: list[TableCell] = row.cells.copy()
            row._cells = [original_cells[i] for i in new_indices]

        # Update coordinates after reordering
        self.normalize()


class MarkdownFile:
    def __init__(self, path: StrPath):
        self._path: Path = Path(path)
        self._content: list[str] = []
        self._tables: list[Table] = []

    def read(self):
        self._content = file_reader(self._path, "lines")

    def __iter__(self):
        return iter(self._tables)

    def set_tables(self):
        """
        Detect tables in _content.
        """
        current_table: list[str] = []
        in_table: bool = False
        start_idx: int = -1

        header_pattern: Pattern = compile(r"^\s*\|(.+\|)+\s*$")
        separator_pattern: Pattern = compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")

        for i, line in enumerate(self._content):
            stripped: str = line.strip()

            if in_table:
                if stripped == "" or (not stripped.startswith("|") and not header_pattern.match(line)):
                    # End of current table
                    if current_table:
                        table: Table = Table.from_file(current_table, start_idx, i)
                        self._tables.append(table)
                        current_table: list[str] = []
                    in_table: bool = False
                else:
                    # Continue collecting table lines
                    current_table.append(line)
            else:
                # Look for table header + separator line
                if (header_pattern.match(line)
                        and i + 1 < len(self._content)
                        and separator_pattern.match(self._content[i + 1])):
                    in_table: bool = True
                    start_idx: int = i
                    current_table: list[str] = [line, self._content[i + 1]]

        # If file ends inside a table
        if in_table and current_table:
            table: Table = Table.from_file(current_table, start_idx, len(self._content))
            self._tables.append(table)

    def update_table(self, table: Table):
        # Fixed: Remove lines in correct range
        for index in range(table.stop - 1, table.start - 1, -1):
            if index < len(self._content):
                self._content.pop(index)

        # Insert the updated table
        if table.start <= len(self._content):
            self._content.insert(table.start, str(table))

        else:
            self._content.append(str(table))

    def save(self):
        file_writer(self._path, self._content)


if __name__ == '__main__':
    file: str = "./congestion.md"

    try:
        markdown_file: MarkdownFile = MarkdownFile(file)
        markdown_file.read()
        markdown_file.set_tables()

        tables_found: list[Table] = list(markdown_file)

        if not tables_found:
            logger.warning("No tables found in the file")

        else:
            logger.info(f"Found {len(tables_found)} tables")

        for item in reversed(tables_found):
            logger.debug(f"Processing table from line {item.start} to {item.stop}")
            logger.debug(f"Original table:\n{item}")
            item.fix_borders()

            item.normalize()
            item.split_column_ompr()
            logger.debug(f"After OMPR split:\n{item}")

            item.extract_type_to_new_column(3)  # Column 3 should be the description column after split
            logger.debug(f"After type extraction:\n{item}")

            item.reorder_columns_by_names(["Параметр", "Описание", "Тип", "O/M", "P/R"])
            item.insert_column(5, TableColumn())
            item.get_cell(0, 5).content = "Версия"

            markdown_file.update_table(item)

        markdown_file.save()
        logger.success(f"Файл {file} успешно обработан")

    except FileNotFoundError:
        logger.error(f"File {file} not found")
        raise

    except Exception as e:
        logger.error(f"Error processing file {file}: {e}")
        raise
