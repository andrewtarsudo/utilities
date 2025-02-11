# -*- coding: utf-8 -*-
from pathlib import Path
from re import finditer
from string import digits
from typing import Iterable, Iterator

from loguru import logger

from utilities.common.errors import TableColsTableBorderNotClosedError
from utilities.common.functions import file_writer
from utilities.table_cols import TableAnalyser
from utilities.table_cols.column import TableColumn
from utilities.table_cols.table import Table


class AsciiDocFile:
    def __init__(
            self,
            path: str | Path,
            *,
            content: Iterable[str] = None):
        self._path: Path = Path(path)

        if content is None:
            content: list[str] = []

        else:
            content: list[str] = [*content]

        self._content: list[str] = content

        self._tables: list[tuple[Table, int, int]] = []

    def __str__(self):
        return "\n".join(self._content)

    def __iter__(self):
        return iter(self._content)

    def __len__(self):
        return len(self._content)

    def __getitem__(self, item):
        if isinstance(item, int):
            try:
                _: str = self._content[item]

            except IndexError:
                logger.error(f"Индекс {item} превышает длину файла {self._path}")
                raise

            else:
                return _

        elif isinstance(item, slice):
            start: int = 0 if item.start is None else item.start
            stop: int = len(self) if item.stop is None else item.stop

            return [self._content[index] for index in range(start, stop)]

        else:
            logger.error(
                f"Ключ {item} для файла {self._path} должен быть типа int или slice,"
                f"но получен {type(item)}")
            raise TypeError

    def __setitem__(self, key, value):
        if isinstance(key, int) and isinstance(value, str):
            self._content[key] = value

        else:
            logger.error(
                f"Ключ {key} должен быть типа int, а значение {value} должно быть типа str, "
                f"но получены {type(key)} и {type(value)}")
            raise TypeError

    def table_borders(self) -> Iterator[tuple[int, int]]:
        """Iterates over the table_cols borders signs, '|==='."""
        table_marks: list[int] = [
            index for index, line in enumerate(iter(self))
            if line.startswith("|===")]

        # check if all tables are opened and closed
        # if not, the IndexError is raised
        if len(table_marks) % 2 != 0:
            line_indexes: str = ", ".join(map(str, table_marks))
            logger.error(
                f"В файле {self._path} пропущен символ завершения таблицы '|==='\n"
                f"Найдено {len(table_marks)}: в строках {line_indexes}", tech_writers=True)
            raise TableColsTableBorderNotClosedError

        for i in range(len(table_marks) // 2):
            yield table_marks[2 * i], table_marks[2 * i + 1]

    def set_tables(self):
        """Specifies the tables in the file."""
        PATTERN_OPTIONS: str = r"(\w+=\"[^\"]+\"|%[^,]+)"

        # get the limits by the '|===' lines
        for index, (start, stop) in enumerate(self.table_borders()):
            lines: list[str] = self[start + 1:stop]

            options: dict[str, str | None] = dict()

            # gets the options if specified
            # sign '=' is used for options like 'key="value"'
            # sign '%' is used for options like '%key'
            if start >= 1:
                options_str: str = self[start - 1]
                is_char: bool = any(char in self[start - 1] for char in "=%")
                is_start: bool = options_str.startswith("[")
                is_end: bool = options_str.endswith("]")

                if any(_ is True for _ in (is_char, is_start, is_end)):
                    for m in finditer(PATTERN_OPTIONS, options_str):
                        # separate options due to their format
                        option: str = m.group(1)

                        if option.startswith("%"):
                            options[option] = None

                        else:
                            k, v = option.split("=", 1)
                            options[k] = v[1:-1]

            # check if the table_cols has a specified name
            if start > 2 and self[start - 2].startswith("."):
                name: str = self[start - 2]

            # otherwise, set the name as <filename>_<table_cols order number in the file>
            else:
                name: str = f"{self._path.with_suffix('')}_{index}"

            table: Table = Table(name, index, lines, options)
            table.define_cells()

            # check if the text has distinguished cells
            if len(table.table_cells) > 0:
                self._tables.append((table, start, stop))

            else:
                _: str = "\n".join(iter(table))

                logger.debug(
                    f"Таблица {table.name} не может быть обработана\n"
                    f"Строки:\n{_}")

    def replace_tables(self):
        """Replaces tables with the modified ones."""
        lines: list[str] = self[:]

        for table, start, stop in reversed(self._tables):
            lines: list[str] = [*lines[:start - 1], "\n", str(table), *lines[stop + 1:]]

        self._content = lines

    def fix_tables(self, table_analyser: TableAnalyser):
        """Adds the 'cols' option if not specified."""
        for table, *_ in self._tables:
            table_analyser.nullify()

            # skip table_cols if it has spanned cells
            if table.has_horizontal_span():
                logger.warning(
                    "В таблице есть объединенные горизонтальные ячейки.\n"
                    "На данный момент такие таблицы оставляются как есть.\n"
                    f"Таблица {table.index}, {table.name}")
                continue

            # skip table_cols if it already has cols option
            elif "cols" in table.options and any(digit in table.options.get("cols") for digit in digits):
                continue

            # skip tables if some text has been accidentally processed as table_cols
            elif not bool(table):
                _: str = "\n".join(iter(table))

                logger.warning(
                    f"Не удалось корректно обработать текст:\n{_}")
                continue

            else:
                table_column: TableColumn
                table_analyser._column_parameters = [
                    table_column.column_parameters() for table_column in table.iter_column_items()]
                table_analyser._table_id = f"{self._path.name}, {table.name}"
                table_analyser.inspect_valid()
                table_analyser.set_base_column_widths()
                table_analyser.distribute_rest()
                table.options["cols"] = str(table_analyser)

    def save(self):
        file_writer(self._path, self._content)
