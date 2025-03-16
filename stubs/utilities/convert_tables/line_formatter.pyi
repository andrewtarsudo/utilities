# -*- coding: utf-8 -*-
from typing import MutableSequence
from utilities.common.errors import ConvertTablesEmptyLinesError as ConvertTablesEmptyLinesError


class LineFormatter:
    def __init__(self, remove_spaces: bool, escape_chars: bool) -> None: ...

    def format_lines(self, lines: MutableSequence[str] = None): ...
