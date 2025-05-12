# -*- coding: utf-8 -*-
from pathlib import Path
from pprint import pformat
from typing import MutableMapping

from click import get_app_dir
from loguru import logger

from utilities.common.errors import ConfigFileGeneralKeyError, ConfigFileUpdateKeyError, FileReaderError
from utilities.common.functions import file_reader_type
from utilities.common.shared import BASE_PATH, ConfigType, FileType


class ConfigFile(dict):
    path: Path = BASE_PATH.joinpath("sources/config.toml")
    user_path: Path = get_app_dir("utilities/config")

    # noinspection PyTypeChecker
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

    def read_user_configs(self, suffix: str, file_type: FileType):
        path: Path = Path(self.user_path.with_suffix(suffix))

        try:
            user_kwargs: ConfigType = file_reader_type(path, file_type)

            for k, v in user_kwargs.items():
                self[k] = v

        except FileReaderError:
            logger.debug(f"Пользовательский конфигурационный файл {path.name} не найден или не обработан")

    def get_commands(self, command: str, key: str) -> str | int | float | bool | list[str] | None:
        if command is None:
            return

        try:
            return self["commands"][command][key]

        except (AttributeError, KeyError):
            logger.debug(f"Команда {command}, ключ {key}")
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
