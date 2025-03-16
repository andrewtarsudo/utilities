# -*- coding: utf-8 -*-
from time import perf_counter_ns
from types import TracebackType
from typing import Any, ContextManager

from click.termui import echo

from utilities.common.errors import TimerRunningError, TimerStoppedError


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


class Timer(ContextManager):
    """Time your code using a class, context manager, or decorator"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._start_time = None
            cls._instance._end_time = None
            cls._instance._elapsed_time = 0

            for k, v in kwargs.items():
                setattr(cls._instance, f"_{k}", v)

        return cls._instance

    def start(self) -> None:
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerRunningError

        self._start_time = perf_counter_ns()
        self._end_time = None

    def pause(self):
        if self._start_time is None:
            raise TimerStoppedError

        self._end_time = perf_counter_ns()
        self._elapsed_time += self._end_time - self._start_time
        self._start_time = None

    def stop(self):
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            raise TimerStoppedError

        # Calculate elapsed time
        self.pause()

        # Report elapsed time
        echo(process_timing(self._elapsed_time))
        self._start_time = None
        self._end_time = None
        self._elapsed_time = 0

    def __enter__(self):
        """Start a new timer as a context manager"""
        self.start()
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None, /) -> None:
        """Stop the context manager timer"""
        echo(
            f"{exc_type.__class__.__name__}, {str(exc_value)}"
            f"\n{traceback.tb_lineno}{traceback.tb_lasti}"
            f"\n{traceback.tb_frame}")
        self.pause()
