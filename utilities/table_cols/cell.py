# -*- coding: utf-8 -*-
from collections import Counter
from re import DOTALL, sub
from string import ascii_letters, digits

from slugify import slugify

from utilities.table_cols.coordinate import TableCoordinate


def fix_length(text: str):
    NARROW: str = ":;.\",!'`/"
    MEDIUM: str = "{}[]$#()"

    counter: Counter = Counter(text)

    narrow: int = sum((counter.get(_, 0) for _ in NARROW), 0)
    medium: int = sum((counter.get(_, 0) for _ in MEDIUM), 0)

    return len(text) - 2 * narrow - medium


class TableCell:
    """Class to represent the table_cols cell."""

    def __init__(
            self,
            table_coordinate: TableCoordinate,
            text: str = None,
            row_modifier: int = 1,
            column_modifier: int = 1):
        self._table_coordinate: TableCoordinate = table_coordinate
        self._text: str = text
        self._row_modifier: int = row_modifier
        self._column_modifier: int = column_modifier

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
            r"[\<\>\[\]\{\}]": r"",
        }

        _: str = self._text

        for k, v in SUBS.items():
            _: str = sub(k, v, _, DOTALL)

        return _

    def processed_text(self):
        """Gets the raw text modified for the standards and recommendations."""
        # implemented to process names of standards and specifications as a single word
        replacements: tuple[tuple[str, str], ...] = (
            ("3GPP ", "3GPP_"),
            ("TS ", "TS_"),
            ("RFC ", "RFC"),
            ("ITU-T ", "ITU-T_"),
            ("Recommendation ", "Recommendation_"),
            ("GSM ", "GSM_")
        )

        if self.is_spaced():
            separator: str = " "

        else:
            separator: str = "-"

        _: str = slugify(
            self.raw_text,
            replacements=replacements,
            separator=separator,
            lowercase=False,
            allow_unicode=True,
            stopwords=["br"])

        if _ == "":
            return ""

        else:
            return _.strip()

    @property
    def occupied_elements(self) -> int:
        """Gets the number of real cells united to this one with spans."""
        return self._row_modifier * self._column_modifier

    def __bool__(self):
        return self._text is not None and self._text != ""

    def is_spaced(self) -> bool:
        """Indicates if the text has spaces.

        Implemented to define the cells that represent parameter names.
        Such cells should be as wide as required and as narrow as possible.
        """
        if not bool(self):
            return False

        else:
            return " " in self._text.strip()

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

    @property
    def minimum_length(self) -> int:
        """Gets the minimum width of the column to place the text without hyphenation.

        Based on the maximum length of separate words.
        """
        if not bool(self):
            return 0

        elif self.is_spaced():
            return max(map(fix_length, self.processed_text().split()))

        else:
            return fix_length(self.processed_text())

    @property
    def preferred_length(self) -> int:
        """Gets the complete length of the text counting all symbols."""
        return len(self.processed_text())

    def __len__(self):
        return self.preferred_length

    @property
    def text(self):
        return self._text
