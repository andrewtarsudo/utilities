# -*- coding: utf-8 -*-
from typing import NamedTuple

from repair_link.general.const import prepare_logging


class InputUser(NamedTuple):
    # noinspection PyUnresolvedReferences
    """
    The user input values.

    Attributes
    ----------
    pathdir : str
        The path to the directory.
    dry_run : bool
        The flag not to modify files.
    keep_log : bool
        The flag to store the log file.
    no_result : bool
        The flag to remove the file with modifications.
    anchor_validation : bool
        The flag to validate anchors in the text files.
    separate_languages : bool
        The flag to process files separately according to their languages.
    skip_en : bool
        The flag to ignore English files.

    """
    pathdir: str | None
    dry_run: bool
    keep_log: bool
    no_result: bool
    anchor_validation: bool
    separate_languages: bool
    skip_en: bool

    def __str__(self):
        return prepare_logging((f"{k}={v}" for k, v in self._asdict().items()), "")

    def __repr__(self):
        return f"<{self.__class__.__name__}(\n{self._asdict()}\n)>"

    def __bool__(self):
        return self.pathdir is not None
