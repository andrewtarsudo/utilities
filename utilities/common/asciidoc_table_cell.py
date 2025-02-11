# -*- coding: utf-8 -*-
from re import DOTALL, sub
from string import ascii_letters, digits

from utilities.common.table_coordinate import TableCoordinate


class TableCell:
    """Class to represent the table_cols cell."""

    def __init__(
            self,
            table_coordinate: TableCoordinate,
            text: str = None,
            row_multiplier: int = 1,
            column_multiplier: int = 1):
        self._table_coordinate: TableCoordinate = table_coordinate
        self._text: str = text
        self._row_multiplier: int = row_multiplier
        self._column_multiplier: int = column_multiplier

    def __hash__(self):
        return hash(self._table_coordinate.coord)

    @property
    def raw_text(self):
        """Gets the text without decorations and modifications like styling, links, anchors, html tags, etc."""
        # check if the text has any characters or digits
        # if not, keep as is since it means the text is a set of punctuation marks
        LETTERS: str = f"{ascii_letters}{digits}АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя"

        if not any(char in LETTERS for char in self._text):
            return self._text

        SUBS: dict[str, str] = {
            r"pass:q\[(.*?)\]": r"\1",
            r"\[\[.*?\]\]": r"",
            r"<[^>]*?>(.+?)</[^>]*?>": r"\1",
            r"[&\{]nbsp[;}]": r"_",
            r"\[.*?\]#(.*?)#": r"\1",
            r"https?[^)\[]*?": r"",
            r"<<[^,]*?,([^>]*?)>>": r"\1",
            r"\[\.?[\[#].*?]": r"",
            r"link:[^\[]*": r"",
            r"[&\{][lg]t[;}]": r"_",
            r"[\<\>\[\]\{\}]": r""}

        _: str = self._text

        for k, v in SUBS.items():
            _: str = sub(k, v, _, DOTALL)

        return _

    @property
    def occupied_elements(self) -> int:
        """Gets the number of real cells united to this one with spans."""
        return self._row_multiplier * self._column_multiplier

    def __bool__(self):
        return self._text is not None and self._text != ""

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
            f"{self._table_coordinate.__class__.__name__}({self._table_coordinate})\n{self._text}")

    def __str__(self) -> str:
        if not bool(self):
            return "| "

        else:
            return f"|{self._text}"

    def __len__(self):
        return len(self._text)

    @property
    def text(self):
        return self._text
