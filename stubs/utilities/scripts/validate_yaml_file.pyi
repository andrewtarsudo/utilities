# -*- coding: utf-8 -*-
from click.core import Context as Context
from typing import Any, Iterable, Mapping
from utilities.common.shared import FAIL_COLOR as FAIL_COLOR, HELP as HELP, NORMAL_COLOR as NORMAL_COLOR, \
    PASS_COLOR as PASS_COLOR, StrPath as StrPath, pretty_print as pretty_print
from utilities.common.functions import ReaderMode as ReaderMode, file_reader as file_reader
from utilities.scripts.cli import SwitchArgsAPIGroup as SwitchArgsAPIGroup, clear_logs as clear_logs, \
    cli as cli


def determine_key(item: Mapping, keys: Iterable[str]): ...


def detect_extra_keys(item: Mapping[str, Any]): ...


def inspect_settings(
        content: Mapping[str, Any],
        verbose: bool,
        warnings: Iterable[str] = None,
        messages: Iterable[str] = None): ...


def inspect_legal(
        content: Mapping[str, Any],
        verbose: bool,
        warnings: Iterable[str] = None,
        messages: Iterable[str] = None): ...


def inspect_sections(
        content: Mapping[str, Any],
        verbose: bool,
        warnings: Iterable[str] = None,
        messages: Iterable[str] = None): ...


def validate(root: StrPath, lines: Iterable[str], out: str | None = None, verbose: bool = False): ...


def validate_json_scheme() -> None: ...


def validate_yaml_command(
        ctx: Context,
        yaml_file: StrPath,
        output: StrPath = None,
        verbose: bool = False,
        keep_logs: bool = False): ...
