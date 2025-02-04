# -*- coding: utf-8 -*-
from collections import Counter
from re import sub
from string import ascii_letters, digits

from slugify import slugify

from utilities.table_cols.coordinate import TableCoordinate


def length_offset(line: str) -> int:
    """Adds the correction for narrow symbols that require little space.

    The symbols are punctuation marks.
    The function is taken out of the class for easier testing.
    """
    NARROW_SYMBOLS: str = ".[]()\\/:;,{}'\"|"
    narrow_offset: int = (sum(Counter(line).get(char, 0) for char in NARROW_SYMBOLS) + 1) // 2

    return len(line) - narrow_offset


class TableCell:
    """Class to represent the table_cols cell."""

    def __init__(
            self,
            table_coordinate: TableCoordinate,
            text: str = None,
            row_modifier: int = 1,
            column_modifier: int = 1):
        self.table_coordinate: TableCoordinate = table_coordinate
        self.text: str = text
        self.row_modifier: int = row_modifier
        self.column_modifier: int = column_modifier

    def __hash__(self):
        return hash(self.table_coordinate.coord)

    def raw_text(self):
        """Gets the text without decorations and modifications like styling, links, anchors, html tags, etc."""
        # check if the text has any characters or digits
        # if not, keep as is since it means the text is a set of punctuation marks
        sense_letters: str = f"{ascii_letters}{digits}АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя"

        if not any(char in sense_letters for char in self.text):
            return self.text

        SUBS: dict[str, str] = {
            r"pass:q\[(.*?)\]": r"\1",
            r"<[^>]*?>(.+?)</[^>]*?>": r"\1",
            r"[&\{]nbsp[;}]": "_",
            r"https?[^)\[]*?": "",
            r"<<[^,]*?,([^>]*?)>>": r"\1",
            r"\[\.?[\[#].*?]": "",
            r"link:[^\[]*": r""
        }

        # implemented to process names of standards and specifications as a single word
        replacements: tuple[tuple[str, str], ...] = (
            ("3GPP ", "3GPP_"),
            ("TS ", "TS_"),
            ("RFC ", "RFC"),
            ("ITU-T ", "ITU-T_"),
            ("Recommendation ", "Recommendation_"),
            ("GSM ", "GSM_")
        )
        _: str = self.text

        for k, v in SUBS.items():
            _: str = sub(k, v, _)

        if self.is_spaced():
            separator: str = " "

        else:
            separator: str = "-"

        raw_text: str = slugify(
            _,
            replacements=replacements,
            separator=separator,
            lowercase=False,
            allow_unicode=True,
            stopwords=["br"])

        if raw_text == "":
            return ""

        else:
            return raw_text.strip()

    @property
    def occupied_elements(self) -> int:
        """Gets the number of real cells united to this one with spans."""
        return self.row_modifier * self.column_modifier

    def __bool__(self):
        return self.text is not None and self.text != ""

    def is_spaced(self) -> bool:
        """Indicates if the text has spaces.

        Implemented to define the cells that represent parameter names.
        Such cells should be as wide as required and as narrow as possible.
        """
        if not bool(self):
            return False

        else:
            return " " in self.text.strip()

    @property
    def coord(self) -> tuple[int, int]:
        """Gets the coordinates."""
        return self.table_coordinate.coord

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
            f"{self.table_coordinate.__class__.__name__}({self.table_coordinate})\n{self.text}")

    def __str__(self) -> str:
        if not bool(self):
            return "| "

        else:
            return f"|{self.text}"

    def minimum_length(self) -> int:
        """Gets the minimum width of the column to place the text without hyphenation.

        Based on the maximum length of separate words.
        """
        if not bool(self):
            return 0

        elif self.is_spaced():
            return max(map(length_offset, self.raw_text().split()))

        else:
            return length_offset(self.raw_text())

    def preferred_length(self) -> int:
        """Gets the complete length of the text counting all symbols."""
        return len(self.raw_text())

    def __len__(self):
        return self.preferred_length()
