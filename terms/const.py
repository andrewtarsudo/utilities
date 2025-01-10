# -*- coding: utf-8 -*-
from enum import Enum
from pathlib import Path
from typing import Iterable

from loguru import logger


def write_file(file_path: str | Path, content: str | Iterable[str]):
    if not isinstance(content, str):
        content: str = "\n".join(content)

    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    Path(file_path).touch(exist_ok=True)

    try:
        with open(file_path, "w") as f:
            f.write(content)
            logger.debug(f"Файл {file_path} записан")

    except FileNotFoundError:
        logger.error(f"Файл {file_path} не найден")
        raise

    except PermissionError:
        logger.error(f"Недостаточно прав для записи в файл {file_path}")
        raise

    except RuntimeError:
        logger.error(f"Истекло время записи в файл {file_path}")
        raise

    except OSError as e:
        logger.debug(f"Ошибка {e.__class__.__name__}: {e.strerror}")
        raise


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
