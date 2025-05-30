# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Any, Mapping, Sequence

from strictyaml.scalar import Str
from strictyaml.compound import Map, MapPattern

from utilities.common.config_file import config_file
from utilities.common.functions import file_reader_type, pretty_print
from utilities.common.shared import BASE_PATH


class ArgsHelpDict(dict):
    def __init__(self, schema: MapPattern = None):
        if schema is None:
            schema: MapPattern = MapPattern(Str(), Map({Str(): Str()}))

        config_path: Path = BASE_PATH.joinpath(config_file.get_general("config_path"))
        content: dict[str, dict[str, str]] = file_reader_type(config_path, "yaml", schema=schema)

        super().__init__()
        self.update(**content)

    def __str__(self):
        return pretty_print(f"{k} = {v}" for k, v in self.items())

    def get_multiple_keys(self, *, dictionary: Mapping[str, Any] = None, keys: Sequence[str] = None):
        if dictionary is None:
            dictionary: Mapping[str, Any] = self

        if not keys:
            return dictionary

        else:
            return self.get_multiple_keys(dictionary=dictionary.get(keys[0]), keys=keys[1:])

    @property
    def max_key(self) -> int:
        return max(len(k) for _, values in self.items() for k, _ in values.items()) + 6


args_help_dict: ArgsHelpDict = ArgsHelpDict()
