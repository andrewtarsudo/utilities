# -*- coding: utf-8 -*-
from enum import Enum


class CustomPort(Enum):
    HTTP = 80
    HTTPS = 443


class CustomScheme(Enum):
    HTTP = 'http'
    HTTPS = 'https'
