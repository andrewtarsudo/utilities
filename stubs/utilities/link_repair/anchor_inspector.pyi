# -*- coding: utf-8 -*-
from utilities.common.shared import pretty_print as pretty_print, separator as separator
from utilities.common.errors import LinkRepairFileInvalidTypeError as LinkRepairFileInvalidTypeError, \
    LinkRepairMissingFileError as LinkRepairMissingFileError
from utilities.common.functions import ReaderMode as ReaderMode, file_reader as file_reader
from utilities.link_repair.const import FileLanguage as FileLanguage, prepare_logging as prepare_logging
from utilities.link_repair.file_dict import TextFile as TextFile


class AnchorInspector:
    def __init__(self) -> None: ...

    def __getitem__(self, item): ...

    def get(self, item): ...

    def __add__(self, other) -> None: ...

    @property
    def dict_ru_files(self) -> dict[TextFile, list[str]]: ...

    @property
    def dict_en_files(self) -> dict[TextFile, list[str]]: ...

    def inspect_inside_file(self, language: FileLanguage): ...

    def all_anchors(self, language: FileLanguage) -> list[str]: ...

    def inspect_all_files(self, language: FileLanguage): ...

    @property
    def dict_changes(self): ...


anchor_inspector: AnchorInspector
