# -*- coding: utf-8 -*-
from re import sub
from typing import MutableSequence

from loguru import logger

from utilities.common.errors import ConvertTablesEmptyLinesError


class LineFormatter:
    def __init__(self, remove_spaces: bool, escape_chars: bool):
        self._remove_spaces: bool = remove_spaces
        self._escape_chars: bool = escape_chars
        self._patterns: dict[str, dict[str, str]] = {
            "remove_spaces": {
                r"\s+": " ",
                r"\s\.": "."},
            "escape_chars": {
                r"([*-_])": r"\\\1",
                r"<(?!/?br>|/?sub>|/?sup>)([^<>]*)(?<!<br)>": r"\\<\1\\>"}}

    def __str__(self):
        _convert_bool: dict[bool, str] = {
            True: "да",
            False: "нет"}

        return (
            f"Параметры форматирования текста\n"
            f"удаление лишних пробелов: {_convert_bool.get(self._remove_spaces)}\n"
            f"экранирование символов '<', '>': {_convert_bool.get(self._escape_chars)}")

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}(remove_spaces = {self._remove_spaces}, escape_chars = {self._escape_chars})>")

    def format_lines(self, lines: MutableSequence[str] = None):
        if lines is None:
            logger.error("Нет строк для модификации")
            raise ConvertTablesEmptyLinesError

        patterns: dict[str, str] = dict()

        if self._remove_spaces:
            patterns.update(self._patterns.get("remove_spaces"))

        if self._escape_chars:
            patterns.update(self._patterns.get("escape_chars"))

        if patterns:
            for index, line in enumerate(lines):
                for k, v in patterns.items():
                    line: str = sub(k, v, line)
                    lines[index] = line

        return list(lines)
