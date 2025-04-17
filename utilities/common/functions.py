# -*- coding: utf-8 -*-
from io import UnsupportedOperation
from json import JSONDecodeError
from os import scandir
from pathlib import Path
from typing import Any, Callable, Iterable

from loguru import logger
from yaml.scanner import ScannerError

from utilities.common.errors import FileReaderError, FileReaderTypeError
from utilities.common.shared import BASE_PATH, FileType, ReaderMode, StrPath


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
        from yaml import safe_load as load_file

        if suffix not in (".yml", ".yaml"):
            logger.error(f"Файл {path.name} должен иметь расширение .json или .json5, но получено {suffix}")
            raise FileReaderTypeError

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

    except ScannerError as e:
        logger.error(
            f"{e.__class__.__name__}: ошибка обработки файла {e.context_mark.name}"
            f"\nв символе {e.context_mark.line + 1}:{e.context_mark.column + 1}")
        raise

    except JSONDecodeError as e:
        logger.error(
            f"{e.__class__.__name__}: ошибка обработки файла {path.name}"
            f"\nв символе {e.lineno + 1}:{e.colno + 1}")
        raise

    except OSError as e:
        logger.error(f"{e.__class__.__name__}: {e.strerror}")
        raise


def check_path(
        path: StrPath,
        ignored_dirs: Iterable[str] = None,
        ignored_files: Iterable[str] = None,
        extensions: Iterable[str] = None,
        language: str | None = None):
    if ignored_dirs is None:
        ignored_dirs: set[str] = set()

    if ignored_files is None:
        ignored_files: set[str] = set()

    path: Path = Path(path)

    is_dir: bool = path.is_dir()
    is_in_ignored_dirs: bool = any(part in ignored_dirs for part in path.parts)
    has_ignored_name: bool = path.name in ignored_dirs
    is_in_ignored_files: bool = path.stem in ignored_files
    has_ignored_extension: bool = path.suffix not in extensions if extensions else False

    if language is None:
        has_ignored_language: bool = False

    elif not language:
        has_ignored_language: bool = len(path.suffixes) == 1

    else:
        has_ignored_language: bool = f".{language}" not in path.suffixes

    conditions: list[bool] = [
        is_dir, is_in_ignored_dirs, has_ignored_name, is_in_ignored_files, has_ignored_extension, has_ignored_language]

    logger.debug(
        f"Проверка пути {path}:"
        f"\nis_dir = {is_dir}"
        f"\nis_in_ignored_dirs = {is_in_ignored_dirs}"
        f"\nhas_ignored_name = {has_ignored_name}"
        f"\nis_in_ignored_files = {is_in_ignored_files}"
        f"\nhas_ignored_extension = {has_ignored_extension}"
        f"\nhas_ignored_language = {has_ignored_language}\n")

    return not any(conditions)


def walk_full(
        path: StrPath, *,
        ignored_dirs: Iterable[str] = None,
        ignored_files: Iterable[str] = None,
        extensions: Iterable[str] = None,
        language: str | None = None,
        root: Path = None,
        results: list[Path] = None):
    path: Path = Path(path).expanduser()

    if root is None:
        root: Path = Path(path)

    if results is None:
        results: list[Path] = []

    for element in scandir(path):
        item: Path = Path(element.path)

        if element.is_dir(follow_symlinks=True):
            walk_full(
                item,
                ignored_dirs=ignored_dirs,
                ignored_files=ignored_files,
                extensions=extensions,
                language=language,
                root=root,
                results=results)

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
