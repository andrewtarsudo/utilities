# -*- coding: utf-8 -*-
from pathlib import Path
from pprint import pformat
from typing import MutableMapping

from loguru import logger

from utilities.common.errors import ConfigFileGeneralKeyError, ConfigFileUpdateKeyError
from utilities.common.functions import file_reader_type
from utilities.common.shared import BASE_PATH, ConfigType


class ConfigFile(dict):
    path: Path = BASE_PATH.joinpath("sources/config.toml")

    def __init__(self):
        kwargs: ConfigType = file_reader_type(self.path, "toml")

        for k, v in kwargs.items():
            if isinstance(v, MutableMapping):
                for key, value in v.items():
                    if value == "!None":
                        v[key] = None

            kwargs[k] = v

        super().__init__(**kwargs)

        logger.debug(pformat(kwargs, indent=2, width=120))

    def get_commands(self, command: str, key: str) -> str | int | float | bool | list[str]:
        try:
            return self["commands"][command][key]

        except (AttributeError, KeyError):
            return self["commands"]["shared"][key]

    def get_general(self, key: str):
        try:
            return self["general"][key]

        except (AttributeError, KeyError):
            logger.error(f"Ключ {key} не найден в разделе 'general' конфигурационного файла")
            raise ConfigFileGeneralKeyError

    def get_update(self, key: str):
        try:
            return self["update"][key]

        except (AttributeError, KeyError):
            logger.error(f"Ключ {key} не найден в разделе 'update' конфигурационного файла")
            raise ConfigFileUpdateKeyError


config_file: ConfigFile = ConfigFile()
