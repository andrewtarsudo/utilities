# -*- coding: utf-8 -*-
from typing import Any, Mapping, Sequence

from utilities.common.functions import file_reader_type, pretty_print
from utilities.common.shared import BASE_PATH


class ArgsHelpDict(dict):
    def __init__(self):
        content: dict[str, dict[str, str]] = file_reader_type(BASE_PATH.joinpath("sources/dict.yaml"), "yaml")

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
        return max(len(k) for _, values in self.items() for k, _ in values.items()) + 2 + 4


args_help_dict: ArgsHelpDict = ArgsHelpDict()
