# -*- coding: utf-8 -*-
from contextlib import ContextDecorator
from time import perf_counter_ns
from typing import Any

from loguru import logger

from common.errors import TimerRunningError, TimerStoppedError


def process_timing(value: int):
    ms: int = value // 10 ** 6
    ms_str: str = f"{ms} мс"

    if ms <= 1000:
        s_str: str = ""
        m_str: str = ""

    else:
        s, ms = divmod(ms, 10 ** 3)

        if s > 60:
            m, s = divmod(s, 60)

            s_str: str = f" / {s} сек"
            m_str: str = f" / {m} мин"

        else:
            s_str: str = f" / {s} сек"
            m_str: str = ""

    return f"Время выполнения: {ms_str}{s_str}{m_str}"


class Timer(ContextDecorator):
    """Time your code using a class, context manager, or decorator"""

    def __init__(self, is_logged: bool = True):
        super().__init__()
        self._start_time: int | None = None
        self._end_time: int | None = None
        self._is_logged: bool = is_logged

    def start(self) -> None:
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerRunningError

        self._start_time = perf_counter_ns()

    def stop(self) -> float:
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            raise TimerStoppedError

        # Calculate elapsed time
        elapsed_time: int = perf_counter_ns() - self._start_time
        self._start_time = None

        # Report elapsed time
        if self._is_logged:
            logger.info(process_timing(elapsed_time))

        return elapsed_time

    def __enter__(self):
        """Start a new timer as a context manager"""
        self.start()
        return self

    def __exit__(self, *exc_info: Any) -> None:
        """Stop the context manager timer"""
        self.stop()
