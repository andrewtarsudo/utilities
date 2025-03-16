# -*- coding: utf-8 -*-
from typing import NamedTuple
from utilities.common.shared import StrPath as StrPath
from utilities.common.errors import TermsInvalidTypeVersionError as TermsInvalidTypeVersionError, \
    TermsInvalidVersionError as TermsInvalidVersionError
from utilities.common.functions import ReaderMode as ReaderMode, file_reader as file_reader


class Version(NamedTuple):
    day: int | str
    month: int | str
    year: int | str

    def __eq__(self, other): ...

    def __ne__(self, other): ...

    def __bool__(self) -> bool: ...

    @classmethod
    def from_string(cls, line: str): ...


class VersionContainer:
    def __init__(self, version_file: StrPath, basic_version_file: StrPath) -> None: ...

    def __eq__(self, other): ...

    def __ne__(self, other): ...

    def __bool__(self) -> bool: ...

    def set_version_basic(self) -> None: ...
