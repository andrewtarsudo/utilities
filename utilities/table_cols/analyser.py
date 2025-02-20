# -*- coding: utf-8 -*-
"""
The module to calculate the widths of the table_cols columns.

The general steps:

1. Divide columns into the group that do not have texts without spaces, Group 1, and others, Group 2.
2. For cells in Group 1, specify the width equal to their preferred one, TableColumnParameters.preferred_length.
3. For cells in Group 2, specify the width equal to their minimum one, TableColumnParameters.minimum_length.
4. If the full page width is not occupied:

    4.1. Calculate the ratios of the columns with spaced texts for the left area proportionally to their
    preferred lengths.

    4.2. Add the proportioned area to the columns with spaced texts.

5. Convert the column width points to the percentages.
6. If the sum of percentages is not 100%, correct it modifying the widest one.
"""

from loguru import logger

from utilities.common.constants import MAX_SYMBOLS, MIN_COLUMN
from utilities.table_cols.column import TableColumnParameters


class TableAnalyser:
    """Class to represent the scheme to specify the cols options of the table_cols."""

    def __init__(self, *, max_symbols: int = None, min_column: int = None):
        if max_symbols is None:
            max_symbols: int = MAX_SYMBOLS

        if min_column is None:
            min_column: int = MIN_COLUMN

        self._max_symbols: int = max_symbols
        self._min_column: int = min_column
        self._columns: dict[int, int] = dict()
        self._column_parameters: list[TableColumnParameters] = []
        self._is_valid: bool | None = None
        self._table_id: str | None = None

    def nullify(self):
        """Deallocates the used resources."""
        self._columns.clear()
        self._column_parameters.clear()
        self._is_valid = None
        self._table_id = None

    def __iter__(self):
        return iter(self._column_parameters)

    def inspect_valid(self):
        """Checks if possible to specify the table_cols column widths.

        If the sum of minimum lengths < max table_cols width = Basic_config::analyser::max_symbols,
        then there is no way to fit the table_cols properly.
        """
        minimum_lengths: int = sum(column_parameters.minimum_length for column_parameters in iter(self))

        if minimum_lengths > self._max_symbols:
            logger.error(
                f"Минимальная допустимая ширина для таблицы, {minimum_lengths}, "
                f"превышает максимально допустимую, {self._max_symbols}\n"
                f"Таблица {self._table_id}")
            self._is_valid = False

        else:
            self._is_valid = True

        logger.debug(f"{self._table_id}: {self._is_valid}")

    def find_base_column_width(self, column_parameters: TableColumnParameters):
        """Determines the column width to use as a base.

        :param column_parameters: The table_cols column attributes.
        :type column_parameters: TableColumnParameters
        :return: The column width to add to the TableAnalyser::_columns.
        :rtype: int
        """
        if self._is_valid and not column_parameters.is_spaced:
            return max((column_parameters.preferred_length, self._min_column))

        else:
            return max((column_parameters.minimum_length, self._min_column))

    def set_base_column_widths(self):
        """Specifies the min base column widths to fit the table_cols."""
        for column_parameters in iter(self):
            value: int = self.find_base_column_width(column_parameters)
            self._columns[column_parameters.index] = value

    def distribute_rest(self):
        """Splits the width points to the columns with the longest texts.

        Points are divided into parts proportional to the preferred lengths.
        """
        if self._is_valid:
            # find the available width points to distribute to the columns with long texts
            rest: int = self._max_symbols - sum(self._columns.values())

            if rest:
                # the ratios to divide the rest
                # according to their preferred lengths minus the corresponding current ones
                ratios: dict[int, int] = dict()

                for column_parameters in iter(self):
                    if column_parameters.is_spaced:
                        index: int = column_parameters.index
                        ratio: int = column_parameters.preferred_length - self._columns[index]

                        if ratio:
                            ratios[index] = ratio

                # if all columns get their preferred lengths
                if not ratios:
                    return

                else:
                    sum_ratios: int = sum(ratios.values())

                    for index, length in ratios.items():
                        # ratios[index] / sum_ratios is a part that each column with 'spaced' text gets additionally
                        self._columns[index] += int(rest * (ratios[index] / sum_ratios))

    @property
    def percentages(self):
        """Converts the absolute values to percentages."""
        sum_values: int = sum(self._columns.values())

        # get percentages
        percents: list[int] = [round(value * 100 / sum_values) for value in self._columns.values()]
        sum_percents: int = sum(percents)

        # if rounding is not good enough
        # find the gap and reduce it using the max percentage
        if sum_percents != 100:
            delta: int = 100 - sum_percents
            index: int = percents.index(max(percents))

            percents[index] += delta

        return percents

    def __bool__(self):
        return self._is_valid

    def __str__(self):
        return ",".join(f"{percent:.0f}%" for percent in self.percentages)

    def __repr__(self):
        return f"<{self.__class__.__name__}({self._table_id})>"
