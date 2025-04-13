# -*- coding: utf-8 -*-
from time import perf_counter_ns
from types import TracebackType
from typing import ContextManager

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
            cls._instance.start_time = None
            cls._instance.end_time = None
            cls._instance.elapsed_times = []
            cls._instance._active = True
            cls._instance._round_number = 0

            for k, v in kwargs.items():
                setattr(cls._instance, f"_{k}", v)

        return cls._instance

    def __call__(self, *args, **kwargs):
        if not self._active:
            print("Таймер остановлен")
            print(self.get_results())

        else:
            if self.start_time is None:
                self.start()

            else:
                self.pause()

    def __bool__(self):
        return self._active

    def start(self) -> None:
        """Start a new timer"""
        if not bool(self):
            raise TimerRunningError

        self.start_time = perf_counter_ns()
        print(f"{self.start_time=}")

    def pause(self):
        if self.start_time is None:
            raise TimerStoppedError

        self.end_time = perf_counter_ns()
        self.elapsed_times.append(self.end_time - self.start_time)
        self._round_number += 1

    def __getitem__(self, item):
        if isinstance(item, (int, slice)):
            return self.elapsed_times[item]

        else:
            raise TypeError

    def stop(self):
        """Stop the timer, and report the elapsed time"""
        self.pause()
        self._active = False

    def get_results(self):
        return ", ".join(map(process_timing, self.elapsed_times))

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
        self.pause()

    def safe_close(self):
        if not bool(self):
            pass

        else:
            if self.start_time is None:
                self.stop()


def dummy_function():
    print("dummy")


if __name__ == '__main__':
    with Timer() as timer:
        dummy_function()
    timer()
    print(timer.get_result())
