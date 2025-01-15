# -*- coding: utf-8 -*-

from importlib import import_module
from pathlib import Path
from sys import version_info

from line_formatter import LineFormatter

from tomllib import TOMLDecodeError, load

from utilities.common.constants import StrPath


class TomlConfig:
    _basic_attrs: tuple[str, ...] = ("folder_tables", "folder_temp")
    _formatting_attrs: tuple[str, ...] = (
        "remove_multispaces",
        "remove_spaces_before_dots",
        "escape_chars",
        "escape_lt_gt"
    )

    def __init__(self, path: StrPath):
        if isinstance(path, str):
            path: Path = Path(path).resolve()
        self._path: Path = path
        self.config_file: dict[str, dict[str, object]] = dict()
        self.read()

    @property
    def default(self) -> dict[str, str | bool]:
        return {
            "folder_tables": "./tables",
            "folder_temp": "./temp",
            "remove_multispaces": True,
            "remove_spaces_before_dots": True,
            "escape_chars": False,
            "escape_lt_gt": True
        }

    def __getitem__(self, item) -> str | bool:
        if item in [*self._basic_attrs, *self._formatting_attrs]:
            if item in self._basic_attrs:
                value: str | None = self.config_file.get("basic").get(item)
            else:
                value: bool | None = self.config_file.get("formatting").get(item)

            if value is None:
                value: str | bool = self.default.get(item)
            return value

        else:
            raise KeyError

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.config_file.items()})>"

    def __str__(self):
        _config = [f"{k}: {v}" for k, v in self.config_file.items()]
        return ", ".join(_config)

    def read(self):
        try:
            with open(self._path, "rb") as f:
                self.config_file = load(f)

        except (FileNotFoundError, TOMLDecodeError):
            self.config_file = {
                "basic": {
                    "folder_tables": "./tables",
                    "folder_temp": "./_temp"
                },
                "formatting": {
                    "remove_multispaces": True,
                    "remove_spaces_before_dots": True,
                    "escape_chars": False,
                    "escape_lt_gt": True
                }
            }

    def formatting(self) -> LineFormatter:
        _: list[str | bool] = [self[attr] for attr in self._formatting_attrs]
        return LineFormatter(*_)
