# -*- coding: utf-8 -*-
from pathlib import Path

from click.core import Context, Parameter
from click.shell_completion import CompletionItem

from utilities.common.shared import ADOC_EXTENSION, MD_EXTENSION


# noinspection PyUnusedLocal
def file_completion(ctx: Context, parameter: Parameter, incomplete: str):
    base_path: Path = Path.cwd()
    paths: list[str] = []

    for path in base_path.rglob(f"{incomplete}*"):
        if path.is_file() and Path(path).suffix in (MD_EXTENSION, ADOC_EXTENSION):
            paths.append(path.as_posix())

    return [CompletionItem(path) for path in paths]


# noinspection PyUnusedLocal
def dir_completion(ctx: Context, parameter: Parameter, incomplete: str):
    base_path: Path = Path.cwd()
    paths: list[str] = []

    for path in base_path.rglob(f"{incomplete}*"):
        if path.is_dir():
            paths.append(path.as_posix())

    return [CompletionItem(path) for path in paths]


# noinspection PyUnusedLocal
def doc_completion(ctx: Context, parameter: Parameter, incomplete: str):
    base_path: Path = Path.cwd()
    paths: list[str] = []

    for path in base_path.rglob(f"{incomplete}*"):
        if path.is_file() and Path(path).suffix in (".docx", ".docm"):
            paths.append(path.as_posix())

    return [CompletionItem(path) for path in paths]


# noinspection PyUnusedLocal
def file_dir_completion(ctx: Context, parameter: Parameter, incomplete: str):
    base_path: Path = Path.cwd()
    paths: list[str] = []

    for path in base_path.rglob(f"{incomplete}*"):
        if (path.is_file() and Path(path).suffix in (MD_EXTENSION, ADOC_EXTENSION)) or path.is_dir():
            paths.append(path.as_posix())

    return [CompletionItem(path) for path in paths]


# noinspection PyUnusedLocal
def language_completion(ctx: Context, parameter: Parameter, incomplete: str):
    return [CompletionItem(lang) for lang in ["ru", "en", "fr"] if lang.startswith(incomplete)]
