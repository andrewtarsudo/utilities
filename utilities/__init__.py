# -*- coding: utf-8 -*-

try:
    from typing import Any, Callable
    from rich.console import Console

    echo_func: Callable[[str, Any], None] = Console(force_terminal=True).print

except ModuleNotFoundError | ImportError:
    from loguru import logger
    from click.termui import echo

    logger.debug("Не удалось загрузить модуль rich")

    echo_func: Callable[[str, Any], None] = echo


def echo(message: str, **kwargs):
    echo_func(message, **kwargs)


__all__ = ["echo"]
