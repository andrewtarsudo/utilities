from typing import NamedTuple


class TableCoordinate(NamedTuple):
    row: int
    column: int

    @property
    def coord(self) -> tuple[int, int]: ...

    def __eq__(self, other): ...

    def __ne__(self, other): ...

    @classmethod
    def as_element(cls, number: int, num_columns: int): ...

    def shift(self, row_offset: int = 0, column_offset: int = 0): ...
