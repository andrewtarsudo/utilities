# -*- coding: utf-8 -*-
from pathlib import Path
from typing import MutableMapping

from click.utils import get_app_dir
from loguru import logger
from prettyprinter import pformat

from utilities.common.errors import ConfigFileGeneralKeyError, ConfigFileUpdateKeyError, FileReaderError
from utilities.common.functions import file_reader_type
from utilities.common.shared import BASE_PATH, ConfigType, FileType


class ConfigFile(dict):
    path: Path = BASE_PATH.joinpath("sources/config.toml")
    user_path: Path = Path(get_app_dir("utilities")).joinpath("config")

    # noinspection PyTypeChecker
    def __init__(self):
        kwargs: ConfigType = file_reader_type(self.path, "toml")

        self.kwargs: ConfigType = kwargs

        for k, v in kwargs.items():
            if v == "!None":
                kwargs[k] = None

            elif isinstance(v, MutableMapping):
                for key, value in v.items():
                    if value == "!None":
                        v[key] = None

            kwargs[k] = v

        super().__init__(**kwargs)

    def read_user_configs(self, suffix: str, file_type: FileType):
        path: Path = Path(self.user_path.with_suffix(suffix))

        try:
            user_kwargs: ConfigType = file_reader_type(path, file_type)

            for k, v in user_kwargs.items():
                self[k] = v

            logger.debug(pformat(user_kwargs, indent=2, width=120, sort_dict_keys=True))

        except FileReaderError:
            logger.debug(
                f"Пользовательский конфигурационный файл {path.name} не найден или не обработан"
                f"\nПоэтому конфигурация по умолчанию не изменена")

    def get_commands(self, command: str, key: str) -> str | int | float | bool | list[str] | None:
        if command is None:
            return

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
