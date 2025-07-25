# -*- coding: utf-8 -*-
from base64 import b64decode
from functools import cache
from io import UnsupportedOperation
from json import JSONDecodeError
from os import scandir
from pathlib import Path
from sys import platform
from typing import Any, Callable, Iterable

from httpx import HTTPStatusError, InvalidURL, request, RequestError, Response, StreamError, URL
from loguru import logger
from ruamel.yaml.scanner import ScannerError

from utilities.common.errors import FileReaderError, FileReaderTypeError, UpdateProjectIdError
from utilities.common.shared import BASE_PATH, FileType, ReaderMode, StrPath


@cache
def is_windows() -> bool:
    return platform.startswith("win")


@cache
def is_macos() -> bool:
    return platform.startswith("darwin")


@cache
def get_version():
    content: dict[str, dict[str, str]] = file_reader_type(BASE_PATH.joinpath("pyproject.toml"), "toml")
    return content["project"]["version"]


def file_reader(path: StrPath, reader_mode: ReaderMode, *, encoding: str = "utf-8"):
    try:
        with open(Path(path).expanduser().resolve(), "r", encoding=encoding, errors="ignore") as f:
            functions: dict[ReaderMode, Callable] = {
                "string": f.read,
                "lines": f.readlines}

            _: str | list[str] = functions.get(reader_mode)()

        return _

    except FileNotFoundError as e:
        logger.error(f"{e.__class__.__name__}: файл {path} не найден")
        raise

    except PermissionError as e:
        from os import stat

        logger.error(f"{e.__class__.__name__}: недостаточно прав для чтения файла {path}")
        logger.error(f"Доступ: {stat(path).st_mode}")
        raise

    except RuntimeError as e:
        logger.error(f"{e.__class__.__name__}: произошла ошибка обработки во время записи файла {path}")
        raise

    except UnsupportedOperation as e:
        logger.error(f"{e.__class__.__name__}: не поддерживаемая операция с файлом {path}: {e.strerror}")
        raise

    except OSError as e:
        logger.error(f"{e.__class__.__name__}: {e.strerror}")
        raise


def file_writer(path: StrPath, content: str | Iterable[str], *, encoding: str = "utf-8"):
    path: Path = Path(path).expanduser().resolve()
    mode: str = "w" if path.exists() else "x"

    if not isinstance(content, str):
        content: str = "".join(content)

    try:
        with open(path, mode=mode, encoding=encoding, errors="ignore") as f:
            f.write(content)

    except PermissionError as e:
        from os import stat

        logger.error(f"{e.__class__.__name__}: недостаточно прав для записи в файл {path}")
        logger.error(f"Доступ: {stat(path).st_mode}")
        raise

    except RuntimeError as e:
        logger.error(f"{e.__class__.__name__}: произошла ошибка обработки во время записи файла {path}")
        raise

    except UnsupportedOperation as e:
        logger.error(f"{e.__class__.__name__}: не поддерживаемая операция с файлом {path}: {e.strerror}")
        raise

    except OSError as e:
        logger.error(f"{e.__class__.__name__}: {e.strerror}")
        raise


def file_reader_type(path: StrPath, file_type: FileType):
    suffix: str = Path(path).suffix

    if file_type == "json":
        from json import load as load_file

        if suffix not in (".json", ".json5"):
            logger.error(f"Файл {path.name} должен иметь расширение .json или .json5, но получено {suffix}")
            raise FileReaderTypeError

    elif file_type == "yaml":
        from utilities.common.shared import MyYAML

        yaml: MyYAML = MyYAML(typ="safe")
        load_file = yaml.load

        if suffix not in (".yml", ".yaml"):
            logger.error(f"Файл {path.name} должен иметь расширение .json или .json5, но получено {suffix}")
            raise FileReaderTypeError

        options: dict[str, Any]

    elif file_type == "toml":
        from tomllib import load as load_file

        if suffix not in (".toml", ".lock"):
            logger.error(f"Файл {path.name} должен иметь расширение .toml или .lock, но получено {suffix}")
            raise FileReaderTypeError

    else:
        logger.error(f"Тип файла должен быть json, yaml или toml, но получен {file_type}")
        raise FileReaderError

    try:
        with open(path, "rb") as f:
            content: dict[str, Any] = load_file(f)

        return content

    except FileNotFoundError as e:
        logger.error(f"{e.__class__.__name__}: файл {path} не найден")
        raise FileReaderError

    except PermissionError as e:
        from os import stat

        logger.error(f"{e.__class__.__name__}: недостаточно прав для чтения файла {path}")
        logger.error(f"Доступ: {stat(path).st_mode}")
        raise FileReaderError

    except RuntimeError as e:
        logger.error(f"{e.__class__.__name__}: произошла ошибка обработки во время записи файла {path}")
        raise FileReaderError

    except UnsupportedOperation as e:
        logger.error(f"{e.__class__.__name__}: не поддерживаемая операция с файлом {path}: {e.strerror}")
        raise FileReaderError

    except ScannerError as e:
        logger.error(
            f"{e.__class__.__name__}: ошибка обработки файла {e.context_mark.name}"
            f"\nв символе {e.context_mark.line + 1}:{e.context_mark.column + 1}")
        raise FileReaderError

    except JSONDecodeError as e:
        logger.error(
            f"{e.__class__.__name__}: ошибка обработки файла {path.name}"
            f"\nв символе {e.lineno + 1}:{e.colno + 1}")
        raise FileReaderError

    except OSError as e:
        logger.error(f"{e.__class__.__name__}: {e.strerror}")
        raise FileReaderError


def check_path(
        path: StrPath,
        ignored_dirs: Iterable[str] = None,
        ignored_files: Iterable[str] = None,
        extensions: Iterable[str] = None,
        language: str | None = None) -> bool:
    path: Path = Path(path).expanduser()

    # Skip directories (handled in walk_full)
    if path.is_dir():
        return False

    # Check ignored dirs (if any parent folder is ignored)
    if ignored_dirs and any(part in ignored_dirs for part in path.parts):
        return False

    # Check ignored files (exact name match)
    if ignored_files and path.stem in ignored_files:
        return False

    if extensions is not None and extensions and path.suffix not in {*extensions, }:
        return False

    if language is not None:
        suffixes: list[str] = path.suffixes

        if language:
            if f".{language}" not in suffixes:
                return False

        elif any(len(suffix) == 3 and suffix[1:].isalpha() for suffix in suffixes):
            return False

    return True


def walk_full(
        path: StrPath, *,
        ignored_dirs: Iterable[str] = None,
        ignored_files: Iterable[str] = None,
        extensions: Iterable[str] = None,
        language: str | None = None,
        root: Path = None,
        hidden: bool = False,
        results: list[Path] = None):
    path: Path = Path(path).expanduser()

    if root is None:
        root: Path = path

    if results is None:
        results: list[Path] = []

    if ignored_dirs is None:
        ignored_dirs: set[str] = set()

    else:
        ignored_dirs: set[str] = set(ignored_dirs)

    if ignored_files is None:
        ignored_files: set[str] = set()

    else:
        ignored_files: set[str] = set(ignored_files)

    if extensions:
        extensions: set[str] | None = set(f".{extension.lstrip('.')}" for extension in extensions)

    else:
        extensions: set[str] | None = None

    for element in scandir(path):
        item: Path = Path(element.path)

        if element.is_dir():
            if item.name not in ignored_dirs:
                values = walk_full(
                    item,
                    ignored_dirs=ignored_dirs,
                    ignored_files=ignored_files,
                    extensions=extensions,
                    language=language,
                    root=root,
                    hidden=hidden,
                    results=None)
                results.extend(values)

        elif check_path(item, ignored_dirs, ignored_files, extensions, language):
            results.append(item.relative_to(root))

    return results


def pretty_print(values: Iterable[StrPath] = None):
    if values is None or not values:
        return ""

    elif isinstance(values, str):
        return f"{values}"

    else:
        return "\n".join(map(lambda x: str(x).strip(), values))


class GitFile:
    def __init__(
            self,
            file_name: str,
            project_id: int | str, *,
            scheme: str = "https",
            host: str = "gitlab.com",
            port: int = 443,
            query: bytes = b"ref_type=heads",
            method: str = "GET",
            temp_dir: Path = None):
        if not isinstance(project_id, int):
            try:
                project_id: int = int(project_id)

            except ValueError:
                logger.error(
                    "Идентификатор проекта должен быть int или содержать только цифры, "
                    f"isdecimal(), но получено {project_id}")
                raise UpdateProjectIdError

        if temp_dir is None:
            from utilities.common.config_file import config_file

            temp_dir: Path = Path(config_file.get_general("temp_dir")).expanduser()

        self._file_name: str = file_name
        self._project_id: int = project_id
        self._scheme: str = scheme
        self._host: str = host
        self._port: int = port
        self._query: bytes = query
        self._method: str = method
        self._temp_dir: Path = temp_dir
        self._success: bool = False
        self._content: str | None = None

    @property
    def path(self) -> str:
        url_file_name: str = self._file_name.replace(".", "%2E").replace("/", "%2F")
        return f"/api/v4/projects/{self._project_id}/repository/files/{url_file_name}/raw"

    @property
    def url(self) -> URL:
        return URL(
            scheme=self._scheme,
            host=self._host,
            port=self._port,
            path=self.path,
            query=self._query)

    def get_response(self) -> Response:
        return request(method=self._method, url=self.url, timeout=120.0)

    @property
    def json(self) -> dict[str, Any]:
        return self.get_response().json()

    def __bytes__(self):
        return b64decode(self.json.get("content"))

    def __str__(self):
        return self.__bytes__().decode("utf-8")

    def __repr__(self):
        return f"<{self.__class__.__name__}>({str(self)})"

    @property
    def download_destination(self):
        return self._temp_dir.joinpath(self._file_name).expanduser()

    def download(self):
        self.download_destination.parent.mkdir(parents=True, exist_ok=True)
        self.download_destination.touch(exist_ok=True)

        try:
            with open(self.download_destination, "wb") as f:
                response: Response = self.get_response().raise_for_status()
                logger.debug(f"Запрос: {response.request.method} {response.request.url}")

                for chunk in response.iter_bytes():
                    f.write(chunk)

        except HTTPStatusError as e:
            logger.error(
                f"Ошибка HTTP, {e.__class__.__name__}: {e.response}"
                f"\n{e.response.reason_phrase}\n{e.response.status_code}")

        except RequestError as e:
            logger.error(f"Ошибка запроса, {e.__class__.__name__}: {str(e)}")

        except InvalidURL as e:
            logger.error(f"Ошибка URL, {e.__class__.__name__}: {str(e)}")

        except StreamError as e:
            logger.error(f"Ошибка потока, {e.__class__.__name__}: {str(e)}")

        else:
            logger.debug(f"Файл {self.download_destination.name} загружен")
            self._success = True

        self.read()

    def __bool__(self):
        return self._success

    def read(self):
        self._content = file_reader(self.download_destination, "string")

    @property
    def content(self):
        return self._content
