# -*- coding: utf-8 -*-
from typing import Iterable

from utilities.common.functions import file_reader, pretty_print
from utilities.common.shared import StrPath


def clear_values(lines: Iterable[str]) -> list[str]:
    return [line.removesuffix("\n").strip("|").strip() for line in lines]


def clear_from_file(path: StrPath):
    lines: list[str] = file_reader(path, "lines")
    return clear_values(lines)


def format_log(path: StrPath):
    return ",".join(clear_from_file(path))


if __name__ == '__main__':
    file: str = "clear_values"
    print(format_log(file))
