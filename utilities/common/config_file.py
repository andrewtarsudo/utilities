# -*- coding: utf-8 -*-
from pathlib import Path
from typing import TypeAlias

from click.utils import get_app_dir
from loguru import logger
from yaml import safe_dump

from utilities.common.errors import ConfigFileGeneralKeyError, ConfigFileUpdateKeyError, FileReaderError
from utilities.common.functions import file_reader_type
from utilities.common.shared import BASE_PATH, ConfigType, FileType

GetCmdType: TypeAlias = (
        str | int | float | bool | list[str] | None |
        dict[str, dict[str, str | int | float | bool | list[str]]])


class ConfigFile(dict):
    path: Path = BASE_PATH.joinpath("sources/config.yaml")
    user_path: Path = Path(get_app_dir("utilities")).joinpath("config")

    # noinspection PyTypeChecker
    def __init__(self):
        kwargs: ConfigType = file_reader_type(self.path, "yaml")
        super().__init__(**kwargs)

    def read_user_configs(self):
        possible_user_configs: set[tuple[str, FileType]] = {
            (".json", "json"),
            (".json5", "json"),
            (".yml", "yaml"),
            (".yaml", "yaml"),
            (".toml", "toml")}

        for suffix, file_type in possible_user_configs:
            path: Path = Path(self.user_path.with_suffix(suffix))

            try:
                user_kwargs: ConfigType = file_reader_type(path, file_type)

                for k, v in user_kwargs.items():
                    self[k] = v

                logger.debug(safe_dump(user_kwargs, indent=2, width=120, sort_keys=True))

            except FileReaderError:
                logger.debug(f"Пользовательский конфигурационный файл {path.name} не найден или не обработан")

    def get_commands(self, command: str, key: str = None) -> GetCmdType:
        if command is None:
            return

        if key is None:
            try:
                return {**self["commands"][command], **self["commands"]["shared"]}

            except (AttributeError, KeyError):
                return self["commands"]["shared"]

        else:
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
