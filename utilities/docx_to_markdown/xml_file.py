# -*- coding: utf-8 -*-

from pathlib import Path
from shutil import rmtree
from typing import Iterator, TypeAlias
from xml import etree
# noinspection PyProtectedMember
from xml.etree.ElementTree import Element, ElementTree, parse, register_namespace
from zipfile import ZIP_DEFLATED, ZipFile

from toml_parser import LineFormatter, TomlConfig
from .qualified_name import _ns, fqdn
from .xml_formatter import get_all_text

ET: TypeAlias = ElementTree | None
EB: TypeAlias = Element | None
PathLike: TypeAlias = str | Path


class CoreDocument:
    def __init__(self, path: PathLike):
        if isinstance(path, str):
            path: Path = Path(path).resolve()

        self.path: Path = path

        for k, v in _ns.items():
            register_namespace(k, v)

        self._zip_file: ZipFile = ZipFile(self.path, "r", ZIP_DEFLATED)
        self.toml_config: TomlConfig = TomlConfig(Path(__file__).parent.joinpath("config/config.toml"))
        self.path_dir: Path = path.parent.joinpath(self.toml_config["folder_temp"])

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.path})>"

    def __str__(self):
        return f"{self.__class__.__name__}: {self.path}"

    def unarchive(self):
        self.path_dir.mkdir(exist_ok=True)
        self._zip_file.extractall(self.path_dir)

    def delete_temp_archive(self):
        rmtree(self.path_dir, True)

    @property
    def name(self):
        return self.path.stem


class UnzippedFile:
    def __init__(self, name: str, core_document: CoreDocument):
        self._name: str = name
        self._core_document: CoreDocument = core_document

    @property
    def toml_config(self):
        return self._core_document.toml_config

    def __repr__(self):
        return f"<{self.__class__.__name__}({self._name}, {repr(self._core_document)})>," \
               f" {self._core_document.path}"

    def __str__(self):
        return f"{self.__class__.__name__}: {self._name}, {str(self._core_document)}, {self._core_document.path}"

    @property
    def full_path(self) -> Path:
        """The full path to the file in the unpacked archive."""
        return self._core_document.path_dir.joinpath(self._name)


class XmlFile(UnzippedFile):
    def __init__(self, name: str, core_document: CoreDocument):
        super().__init__(name, core_document)
        self.content: EB = parse(self.full_path).getroot()

    def read(self):
        self.content = parse(self.full_path).getroot()

    def get_children_elements(self, tag: str) -> list[Element]:
        return list(self.content.iterdescendants(fqdn(tag)))


class XmlFilePart:
    def __init__(self, tag: str, parent: Element, idx: int | None = None):
        if idx is None:
            idx: int = -1
        self._parent: Element = parent
        self._tag: str = tag
        self._index: int = idx
        self.content: EB = None
        self.read()

    def read(self):
        if self._index == -1:
            self.content = list(self._parent.iterdescendants(fqdn(self._tag)))[0]
        else:
            self.content = list(self._parent.iterdescendants(fqdn(self._tag)))[self._index]

    def get_children_elements(self, tag: str | None = None) -> list[Element]:
        return list(self.content.iterdescendants(fqdn(tag)))


class XmlDocument(XmlFile):
    def __init__(self, core_document: CoreDocument):
        self._name: str = "word/document.xml"
        super().__init__(self._name, core_document)

        _path_dir: Path = self._core_document.path_dir
        _folder_tables: str = self.toml_config["folder_tables"]

        self.table_dir: Path = _path_dir.parent.joinpath(f"{_folder_tables}_{core_document.name}")

        if not self.table_dir.exists():
            self.table_dir.mkdir(parents=True, exist_ok=True)

        for file in self.table_dir.iterdir():
            file.unlink()

    def __repr__(self):
        return f"<{self.__class__.__name__}({repr(self._core_document)})>"

    def __str__(self):
        return f"{self.__class__.__name__}: {self._name}"

    def __len__(self):
        return len(list(self.content.iterdescendants(fqdn("w:tbl"))))

    def __iter__(self) -> Iterator['XmlTable']:
        return iter(XmlTable(self, table_index) for table_index in range(len(self)))

    def parse_document(self):
        xml_table: XmlTable
        for xml_table in iter(self):
            xml_table.read()
            xml_table.write_to_file()


class XmlTable(XmlFilePart):
    def __init__(self, xml_document: XmlDocument, table_index: int):
        tag: str = "w:tbl"
        super().__init__(tag, xml_document.content, table_index)
        self._table_index: int = self._index
        self._xml_document: XmlDocument = xml_document
        self._content: EB = None

    def __str__(self):
        return "\n".join(self._to_lines())

    @property
    def toml_config(self):
        return self._xml_document.toml_config

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

    def _to_lines(self) -> list[str]:
        content: list[str] = []
        for xml_table_row in self.xml_rows:
            xml_table_row.read()
            _: str = " | ".join(xml_table_row.cells_text())
            content.append(f"| {_} |")

        header: str = "|".join(["-----"] * len(self))
        line_formatter: LineFormatter = self.toml_config.formatting()
        formatted_lines = line_formatter.format_lines(content)
        formatted_lines.insert(1, f"|{header}|")
        return formatted_lines

    @property
    def file_path(self) -> Path:
        _file: str = f"table_{self._table_index + 1}.md"
        return self._xml_document.table_dir.joinpath(_file)

    def write_to_file(self):
        if not self.file_path.exists():
            self.file_path.touch(exist_ok=True)

        with open(self.file_path, "w+", encoding="utf-8") as f:
            f.write(str(self))


class XmlTableRow(XmlFilePart):
    def __init__(self, xml_table: XmlTable, row_index: int):
        self._tag = "w:tr"
        super().__init__(self._tag, xml_table.content, row_index)
        self._index: int = row_index
        self._xml_table: XmlTable = xml_table
        self._content: EB = None

    @property
    def _cells(self) -> list[Element]:
        return self.get_children_elements("w:tc")

    def __len__(self):
        return len(self._cells)

    def _cells_text(self) -> list[str]:
        final_text: list[str] = []

        for item in self._cells:
            p_text: list[str] = []

            p: Element
            for p in item.iterdescendants(fqdn("w:p")):
                _text: list[str] = []
                t: Element
                for t in p.iterdescendants(fqdn("w:t")):
                    _text.append(t.text)

                p_text.append("".join(_text))

            final_text.append("<br>".join(p_text))

        return final_text

    def cells_text(self) -> list[str]:
        return [get_all_text(item) for item in self._cells]
