#!/usr/bin/env python3
import os
import re
import sys


class TableCoordinate:
    """Represents a coordinate in a table (row, column)."""

    def __init__(self, row: int, column: int):
        self.row = row
        self.column = column

    def __str__(self) -> str:
        return f"({self.row}, {self.column})"

    def __repr__(self) -> str:
        return f"TableCoordinate(row={self.row}, column={self.column})"


class TableCell:
    """Represents a single cell in a table."""

    def __init__(self, content: str, coordinate: TableCoordinate):
        self.content = content.strip()
        self.coordinate = coordinate

    def __str__(self) -> str:
        return self.content

    def __repr__(self) -> str:
        return f"TableCell(content='{self.content}', coordinate={repr(self.coordinate)})"


class TableRow:
    """Represents a row in a table."""

    def __init__(self, index: int):
        self.index = index
        self.cells: list[TableCell] = []

    def add_cell(self, cell: TableCell) -> None:
        self.cells.append(cell)

    def insert_cell(self, index: int, content: str) -> None:
        """Insert a new cell at the specified index."""
        coord = TableCoordinate(self.index, index)
        new_cell = TableCell(content, coord)
        self.cells.insert(index, new_cell)

    def get_cell(self, column_index: int) -> TableCell | None:
        """Get cell at the specified column index."""
        if 0 <= column_index < len(self.cells):
            return self.cells[column_index]
        return None

    def __str__(self) -> str:
        return " | ".join(str(cell) for cell in self.cells)

    def __repr__(self) -> str:
        return f"TableRow(index={self.index}, cells={len(self.cells)} cells)"


class TableColumn:
    """Represents a column in a table."""

    def __init__(self, index: int, header: str = ""):
        self.index = index
        self.header = header
        self.cells: list[TableCell] = []

    def add_cell(self, cell: TableCell) -> None:
        self.cells.append(cell)

    def __str__(self) -> str:
        return f"Column {self.index}: {self.header}"

    def __repr__(self) -> str:
        return f"TableColumn(index={self.index}, header='{self.header}', cells={len(self.cells)} cells)"


class Table:
    """Represents a table with rows and columns."""

    def __init__(self):
        self.rows: list[TableRow] = []
        self.columns: list[TableColumn] = []
        self.has_header = False
        self.has_separator = False

    def add_row(self, row: TableRow) -> None:
        self.rows.append(row)

        # Update columns based on this row
        while len(self.columns) < len(row.cells):
            self.columns.append(TableColumn(len(self.columns)))

        # Add cells to their respective columns
        for col_idx, cell in enumerate(row.cells):
            if col_idx < len(self.columns):
                self.columns[col_idx].add_cell(cell)

    def add_column(self, index: int, header: str, default_content: str = "") -> None:
        """Add a new column at the specified index."""
        # Shift existing columns
        for col in self.columns:
            if col.index >= index:
                col.index += 1

        # Insert the new column
        new_column = TableColumn(index, header)
        self.columns.insert(index, new_column)

        # Update rows to include the new column
        for row_idx, row in enumerate(self.rows):
            content = header if row_idx == 0 and self.has_header else default_content

            # If this is the separator row, use appropriate format
            if row_idx == 1 and self.has_separator:
                content = "-" * max(3, len(header))

            row.insert_cell(index, content)

    def parse_markdown_table(self, table_str: str) -> None:
        """Parse a markdown table string into the Table object."""
        lines = table_str.strip().split('\n')

        for row_idx, line in enumerate(lines):
            row = TableRow(row_idx)

            # Skip empty lines
            if not line.strip():
                continue

            # Process each cell in the row
            cells = line.split('|')

            # Skip empty first/last cell if it exists
            start_idx = 1 if cells[0].strip() == '' else 0
            end_idx = len(cells) - 1 if cells[-1].strip() == '' else len(cells)

            for col_idx, cell_content in enumerate(cells[start_idx:end_idx]):
                coordinate = TableCoordinate(row_idx, col_idx)
                cell = TableCell(cell_content, coordinate)
                row.add_cell(cell)

            self.add_row(row)

        # Determine if the table has a header and separator
        if len(self.rows) > 1:
            self.has_header = True

            # Check if second row is a separator
            if len(self.rows) > 1:
                is_separator = True
                for cell in self.rows[1].cells:
                    if not re.match(r'^[\s\-:]+$', cell.content):
                        is_separator = False
                        break

                self.has_separator = is_separator

    def parse_asciidoc_table(self, table_str: str) -> None:
        """Parse an AsciiDoc table string into the Table object."""
        lines = table_str.strip().split('\n')

        # Skip |=== markers
        data_lines = [line for line in lines if not line.strip() == '|===']

        for row_idx, line in enumerate(data_lines):
            row = TableRow(row_idx)

            # Process each cell in the row
            if line.startswith('|'):
                cells = line.split('|')

                # Skip the empty first cell from the split
                for col_idx, cell_content in enumerate(cells[1:]):
                    if cell_content.strip():
                        coordinate = TableCoordinate(row_idx, col_idx)
                        cell = TableCell(cell_content, coordinate)
                        row.add_cell(cell)

                self.add_row(row)

        # In AsciiDoc, first row is typically the header
        if self.rows:
            self.has_header = True

    def to_markdown_string(self) -> str:
        """Convert the table to a markdown table string."""
        result = []

        for row_idx, row in enumerate(self.rows):
            cell: TableCell
            cells = [f" {cell.content} " for cell in row.cells]
            line = '|' + '|'.join(cells) + '|'
            result.append(line)

        return '\n'.join(result)

    def to_asciidoc_string(self) -> str:
        """Convert the table to an AsciiDoc table string."""
        result = ['|===']

        for row in self.rows:
            row_cells = []
            for cell in row.cells:
                row_cells.append(f"|{cell.content}")
            result.append(''.join(row_cells))

        result.append('|===')
        return '\n'.join(result)


class File:
    """Represents a file with tables."""

    def __init__(self, filename: str):
        self.filename = filename
        self.content = ""
        self.tables: list[Table] = []
        self.file_type = self._determine_file_type()

    def _determine_file_type(self) -> str:
        """Determine the file type based on extension."""
        ext = os.path.splitext(self.filename)[1].lower()
        if ext == '.md':
            return 'markdown'
        elif ext == '.adoc':
            return 'asciidoc'
        else:
            return 'unknown'

    def read(self) -> bool:
        """Read the file content."""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                self.content = f.read()
            return True
        except Exception as e:
            print(f"Error reading file {self.filename}: {str(e)}")
            return False

    def write(self, output_filename: str | None = None) -> bool:
        """Write the file content to the specified file."""
        if not output_filename:
            name, ext = os.path.splitext(self.filename)
            output_filename = f"{name}_modified{ext}"

        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(self.content)
            print(f"File saved to {output_filename}")
            return True
        except Exception as e:
            print(f"Error writing to file {output_filename}: {str(e)}")
            return False

    def extract_tables(self) -> None:
        """Extract tables from the file content."""
        if self.file_type == 'markdown':
            self._extract_markdown_tables()
        elif self.file_type == 'asciidoc':
            self._extract_asciidoc_tables()

    def _extract_markdown_tables(self) -> None:
        """Extract markdown tables from the content."""
        # Match markdown tables - starts with |, has multiple lines with |
        md_table_pattern = r'\|.*\|[\r\n]+\|[\s\-:]*\|.*[\r\n]+(\|.*\|[\r\n]+)+'

        for match in re.finditer(md_table_pattern, self.content):
            table = Table()
            table.parse_markdown_table(match.group(0))
            self.tables.append((match.span(), table))

    def _extract_asciidoc_tables(self) -> None:
        """Extract AsciiDoc tables from the content."""
        # Match AsciiDoc tables - starts with |===, ends with |===
        adoc_table_pattern = r'\|===[\s\S]*?\|==='

        for match in re.finditer(adoc_table_pattern, self.content):
            table = Table()
            table.parse_asciidoc_table(match.group(0))
            self.tables.append((match.span(), table))

    def add_columns_to_tables(self, second_col_header: str, last_col_header: str, default_content: str = "---") -> None:
        """Add columns to all tables in the file."""
        # Process tables in reverse order to avoid position shifting issues
        for i in range(len(self.tables) - 1, -1, -1):
            span, table = self.tables[i]

            # Add column as second position
            table.add_column(1, second_col_header, default_content)

            # Add column at the end
            table.add_column(len(table.columns), last_col_header, default_content)

            # Update content with the modified table
            if self.file_type == 'markdown':
                table_str = table.to_markdown_string()
            else:  # asciidoc
                table_str = table.to_asciidoc_string()

            self.content = self.content[:span[0]] + table_str + self.content[span[1]:]


def main():
    if len(sys.argv) < 2:
        print("Usage: python table_column_adder.py <filename> [second_col_header] [last_col_header]")
        print("Example: python table_column_adder.py document.md 'Status' 'Notes'")
        return

    filename = sys.argv[1]

    second_col_header = "New Column"
    last_col_header = "Last Column"

    if len(sys.argv) >= 3:
        second_col_header = sys.argv[2]
    if len(sys.argv) >= 4:
        last_col_header = sys.argv[3]

    file = File(filename)

    if file.file_type == 'unknown':
        print(f"Unsupported file extension. Please use .md or .adoc files.")
        return

    if not file.read():
        return

    file.extract_tables()

    if not file.tables:
        print(f"No tables found in {filename}")
        return

    file.add_columns_to_tables(second_col_header, last_col_header)
    file.write()
    print(f"Added columns to {len(file.tables)} tables.")


if __name__ == "__main__":
    main()