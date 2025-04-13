# -*- coding: utf-8 -*-
from collections.abc import Iterable
from pathlib import Path

from click.core import Context

from utilities.common.shared import StrPath


def check_content_common(path: Path): ...


def generate_base_root(path: Path, content_common_index: int): ...


def add_prefix(prefix: str, values: Iterable[StrPath] = None): ...


def list_files_command(
        ctx: Context,
        root_dir: StrPath,
        ignored_dirs: Iterable[str] = None,
        all_dirs: bool = False,
        ignored_files: Iterable[str] = None,
        all_files: bool = False,
        extensions: str = None,
        all_extensions: bool = False,
        language: str = None,
        all_languages: bool = True,
        prefix: str = None,
        no_prefix: bool = False,
        hidden: bool = False,
        ignore_index: bool = False,
        recursive: bool = True,
        auxiliary: bool = False,
        keep_logs: bool = False): ...


def get_files(
        ctx: Context, *,
        files: Iterable[StrPath] = None,
        directory: StrPath = None,
        recursive: bool = True,
        language: str | None = None,
        extensions: str = 'md adoc'): ...
