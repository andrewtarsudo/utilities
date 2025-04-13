# -*- coding: utf-8 -*-
from typing import Any, Mapping, Sequence


class ArgsHelpDict(dict):
    def __init__(self) -> None: ...

    def get_multiple_keys(self, *, dictionary: Mapping[str, Any] = None, keys: Sequence[str] = None): ...

    @property
    def max_key(self) -> int: ...


args_help_dict: ArgsHelpDict
