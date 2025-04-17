# -*- coding: utf-8 -*-
from os import scandir
from pathlib import Path

from click.core import Context, Parameter
from click.shell_completion import CompletionItem

from utilities.common.shared import ADOC_EXTENSION, MD_EXTENSION


# noinspection PyUnusedLocal
def file_completion(ctx: Context, parameter: Parameter, incomplete: str):
    paths: list[str] = []

    for path in scandir("."):
        is_suffix: bool = Path(path).suffix in (MD_EXTENSION, ADOC_EXTENSION)
        is_file: bool = path.is_file(follow_symlinks=True)
        is_incomplete: bool = path.name.startswith(incomplete)

        if is_suffix and is_file and is_incomplete:
            paths.append(path.path)

    return [CompletionItem(path) for path in paths]


# noinspection PyUnusedLocal
def dir_completion(ctx: Context, parameter: Parameter, incomplete: str):
    paths: list[str] = []

    for path in scandir("."):
        is_suffix: bool = Path(path).suffix in (MD_EXTENSION, ADOC_EXTENSION)
        is_dir: bool = path.is_dir(follow_symlinks=True)
        is_incomplete: bool = path.name.startswith(incomplete)

        if is_suffix and is_dir and is_incomplete:
            paths.append(path.path)

    return [CompletionItem(path) for path in paths]


# noinspection PyUnusedLocal
def doc_completion(ctx: Context, parameter: Parameter, incomplete: str):
    paths: list[str] = []

    for path in scandir("."):
        is_suffix: bool = Path(path).suffix in (".docx", ".docm")
        is_file: bool = path.is_file(follow_symlinks=True)
        is_incomplete: bool = path.name.startswith(incomplete)

        if is_suffix and is_file and is_incomplete:
            paths.append(path.path)

    return [CompletionItem(path) for path in paths]


# noinspection PyUnusedLocal
def file_dir_completion(ctx: Context, parameter: Parameter, incomplete: str):
    paths: list[str] = []

    for path in scandir("."):
        is_file: bool = path.is_file() and Path(path).suffix in (MD_EXTENSION, ADOC_EXTENSION)
        is_dir: bool = path.is_dir(follow_symlinks=True)
        is_incomplete: bool = path.name.startswith(incomplete)

        if (is_file or is_dir) and is_incomplete:
            paths.append(path.path)

    return [CompletionItem(path) for path in paths]
