# -*- coding: utf-8 -*-
from re import sub


class LineFormatter:
    def __init__(self):
        self._line: str | None = None
        self._is_remove_multispaces: bool | None = None
        self._is_remove_spaces_before_dots: bool | None = None
        self._is_escape_chars: bool | None = None
        self._is_escape_lt_gt: bool | None = None

    @property
    def line(self):
        return self._line

    @line.setter
    def line(self, value):
        self._line = value

    def __bool__(self):
        return self._line is not None

    def modify_line(self, pattern_from: str, pattern_to: str, is_applied: bool = True):
        if not is_applied:
            return

        else:
            self._line = sub(pattern_from, pattern_to, self._line)

    def format_line(self):
        formatting_params: tuple[tuple[str, str, bool], ...] = (
            (r"\s+", " ", self._is_remove_multispaces),
            (r"([*-_])", r"\\\1", self._is_escape_chars),
            (r"\s\.", ".", self._is_remove_spaces_before_dots),
            (r"<(?!/?br>|/?sub>|/?sup>)([^<>]*)(?<!<br)>", r"\\<\1\\>", self._is_escape_lt_gt)
        )

        for param in formatting_params:
            pattern_from, pattern_to, is_applied = param
            self.modify_line(pattern_from, pattern_to, is_applied)
