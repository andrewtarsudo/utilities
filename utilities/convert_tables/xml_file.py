# -*- coding: utf-8 -*-
from pathlib import Path
from shutil import rmtree
from typing import Iterator
# noinspection PyProtectedMember
from xml.etree.ElementTree import Element, parse, register_namespace
from zipfile import ZIP_DEFLATED, ZipFile

from loguru import logger

from utilities.common.constants import StrPath
from utilities.convert_tables.line_formatter import LineFormatter
from utilities.convert_tables.qualified_name import _ns, fqdn
from utilities.convert_tables.xml_formatter import get_all_text


class CoreDocument:
    def __init__(self, file: StrPath, temp_dir: StrPath):
        self.file: Path = Path(file).resolve()

        for k, v in _ns.items():
            register_namespace(k, v)

        self._zip_file: ZipFile = ZipFile(self.file, "r", ZIP_DEFLATED)
        self.temp_dir: Path = Path(temp_dir).resolve()

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.file})>"

    def __str__(self):
        return f"{self.__class__.__name__}: {self.file}"

    def unarchive(self):
        self.temp_dir.mkdir(exist_ok=True)
        self._zip_file.extractall(self.temp_dir)

    def delete_temp_archive(self):
        rmtree(self.temp_dir, True)

    @property
    def name(self):
        return self.file.stem


class UnzippedFile:
    def __init__(self, name: str, core_document: CoreDocument):
        self._name: str = name
        self._core_document: CoreDocument = core_document

    def __repr__(self):
        return f"<{self.__class__.__name__}({self._name}, {repr(self._core_document)})>," \
               f" {self._core_document.file}"

    def __str__(self):
        return f"{self.__class__.__name__}: {self._name}, {str(self._core_document)}, {self._core_document.file}"

    @property
    def full_path(self) -> Path:
        """The full path to the file in the unpacked archive."""
        return self._core_document.temp_dir.joinpath(self._name)


class XmlFile(UnzippedFile):
    def __init__(self, name: str, core_document: CoreDocument):
        super().__init__(name, core_document)
        self.content: Element = parse(self.full_path).getroot()

    def read(self):
        self.content = parse(self.full_path).getroot()

    def get_children_elements(self, tag: str) -> list[Element]:
        return list(self.content.iter(fqdn(tag)))


class XmlFilePart:
    def __init__(self, tag: str, parent: Element, idx: int | None = None):
        if idx is None:
            idx: int = -1
        self._parent: Element = parent
        self._tag: str = tag
        self._index: int = idx
        self.content: Element | None = None
        self.read()

    def read(self):
        if self._index == -1:
            self.content = list(self._parent.iter(fqdn(self._tag)))[0]

        else:
            self.content = list(self._parent.iter(fqdn(self._tag)))[self._index]

    def get_children_elements(self, tag: str | None = None) -> list[Element]:
        return list(self.content.iter(fqdn(tag)))


class XmlDocument(XmlFile):
    def __init__(self, core_document: CoreDocument, tables_dir: StrPath):
        self._name: str = "word/document.xml"
        super().__init__(self._name, core_document)

        self.tables_dir: Path = Path(tables_dir).resolve()

        if not self.tables_dir.exists():
            self.tables_dir.mkdir(parents=True, exist_ok=True)

        for file in self.tables_dir.iterdir():
            file.unlink()

    def __repr__(self):
        return f"<{self.__class__.__name__}({repr(self._core_document)})>"

    def __str__(self):
        return f"{self.__class__.__name__}: {self._name}"

    def __len__(self):
        return len(list(self.content.iter(fqdn("w:tbl"))))

    def __iter__(self) -> Iterator['XmlTable']:
        return iter(XmlTable(self, table_index) for table_index in range(len(self)))

    def parse_document(self, line_formatter: LineFormatter):
        for xml_table in iter(self):
            xml_table.read()
            xml_table.set_lines(line_formatter)
            xml_table.write_to_file()

        logger.info(f"В директорию {self.tables_dir} записано {len(self)} обработанных таблиц")


class XmlTable(XmlFilePart):
    def __init__(self, xml_document: XmlDocument, table_index: int):
        tag: str = "w:tbl"
        super().__init__(tag, xml_document.content, table_index)
        self._table_index: int = self._index
        self._xml_document: XmlDocument = xml_document
        self._lines: list[str] = []

    def __str__(self):
        return "\n".join(self._lines)

    @property
    def _num_rows(self) -> int:
        return len(self.get_children_elements("w:tr"))

    def __iter__(self):
        return iter(XmlTableRow(self, row_index) for row_index in range(self._num_rows))

    @property
    def xml_rows(self) -> list['XmlTableRow']:
        return list(iter(self))

    def __len__(self):
        return len(self.xml_rows[0])

    def set_lines(self, line_formatter: LineFormatter):
        content: list[str] = []

        for xml_table_row in self.xml_rows:
            xml_table_row.read()
            _: str = " | ".join(xml_table_row.cells_text())
            content.append(f"| {_} |")

        header: str = "|".join(["-----"] * len(self))
        self._lines = line_formatter.format_lines(content)
        self._lines.insert(1, f"|{header}|")

    def write_to_file(self):
        file_path: Path = self._xml_document.tables_dir.joinpath(f"table_{self._table_index + 1}.md")

        if not file_path.exists():
            file_path.touch(exist_ok=True)

        with open(file_path, "w+", encoding="utf-8") as f:
            f.write(str(self))

        logger.debug(f"Записан файл {file_path}")


class XmlTableRow(XmlFilePart):
    def __init__(self, xml_table: XmlTable, row_index: int):
        self._tag = "w:tr"
        super().__init__(self._tag, xml_table.content, row_index)
        self._index: int = row_index

    @property
    def _cells(self) -> list[Element]:
        return self.get_children_elements("w:tc")

    def __len__(self):
        return len(self._cells)

    def cells_text(self) -> list[str]:
        return [get_all_text(item) for item in self._cells]
