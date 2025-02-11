# -*- coding: utf-8 -*-
from enum import Enum


class CustomPort(Enum):
    HTTP = 80
    HTTPS = 443

    def __str__(self):
        return f"{self.__class__.__name__}.{self._value_}"

    def __repr__(self):
        return f"<{self.__class__.__name__}.{self._name_}>"


class CustomScheme(Enum):
    HTTP = "http"
    HTTPS = "https"

    def __str__(self):
        return f"{self.__class__.__name__}.{self._value_}"

    def __repr__(self):
        return f"<{self.__class__.__name__}.{self._name_}>"
