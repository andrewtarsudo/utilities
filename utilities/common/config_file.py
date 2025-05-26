# -*- coding: utf-8 -*-
from pathlib import Path
from typing import TypeAlias

from click.utils import get_app_dir
from loguru import logger

from utilities.common.errors import ConfigFileGeneralKeyError, ConfigFileUpdateKeyError, FileReaderError
from utilities.common.functions import file_reader, file_reader_type, pretty_print
from utilities.common.shared import BASE_PATH, ConfigType, FileType, StrPath

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
        self._is_user_config: bool = None
        self._user_config: StrPath | None = None
        self.read_user_configs()

    def __str__(self):
        system_config: str = file_reader(self.path, "string")
        system_config_label: str = "Системная конфигурация:\n"
        lines: list[str] = [system_config_label, system_config, "\n"]

        if self._is_user_config:
            user_config: str = file_reader(self.user_path, "string")
            user_config_label: str = f"Пользовательская конфигурация ({self._user_config.as_posix()}):\n"

            lines.append(user_config_label)
            lines.append(user_config)

        return pretty_print(lines)

    def read_user_configs(self):
        possible_user_configs: set[tuple[str, FileType]] = {
            (".json", "json"),
            (".json5", "json"),
            (".yml", "yaml"),
            (".yaml", "yaml"),
            (".toml", "toml")}

        for suffix, file_type in possible_user_configs:
            path: Path = Path(self.user_path.with_suffix(suffix))

            if path.exists():
                logger.debug(f"Обнаружен пользовательский конфигурационный файл {path.name}")

                try:
                    user_kwargs: ConfigType = file_reader_type(path, file_type)

                    for k, v in user_kwargs.items():
                        self[k] = v

                    self._is_user_config = True
                    self._user_config: Path = path
                    break

                except FileReaderError:
                    logger.debug(f"Пользовательский конфигурационный файл {path.name} не обработан")
                    self._is_user_config = False

            else:
                logger.debug(f"Пользовательский конфигурационный файл {path.name} не найден")
                continue

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
