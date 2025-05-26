# -*- coding: utf-8 -*-
from typing import Iterable

from loguru import logger

from utilities.common.shared import StrPath

MAX_LINE: int = 0


def from_file(file: StrPath):
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        content: list[str] = [line.strip() for line in f.readlines() if line.strip()]
    return content


def split_line(line: str) -> tuple[str, ...]:
    return tuple(line.strip().split(maxsplit=1))


def normalize_lines(
        lines: Iterable[str] = None, *,
        separator: str = "\t\t",
        indent: int = 0,
        terminal_width: int | None = None):
    if lines is None:
        logger.error("Строки пусты")
        return

    split_lines: list[tuple[str, ...]] = list(map(split_line, lines))

    max_length: int = max(len(k[0]) for k in split_lines)

    if not isinstance(indent, int) or indent < 0:
        indent: int = 0

    if not isinstance(terminal_width, int) or terminal_width < 0:
        terminal_width: int | None = None

    indentation: str = " " * indent

    formatted_lines: list[str] = []

    for arg, description in split_lines:
        result_line: str = f"{indentation}{arg:<{max_length}}{separator}{description}"

        if terminal_width is not None:
            _: list[str] = [*result_line]
            _.insert(terminal_width + 1, "\n")
            result_line: str = "".join(_)

        formatted_lines.append(result_line)

    return "\n".join(formatted_lines)
