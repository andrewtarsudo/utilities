# -*- coding: utf-8 -*-
from pathlib import Path
from sys import platform
from typing import NamedTuple


class SystemInfo(NamedTuple):
    prog: str
    folder: Path

    @classmethod
    def generate(cls):
        if platform.startswith("win"):
            prog: str = f"{Path(__file__).parent.name}.exe"
            folder: Path = Path.home().joinpath("AppData/Local/TechWritersUtilities")

        elif platform.startswith("darwin"):
            prog: str = f"{Path(__file__).parent.name}"
            folder: Path = Path.home().joinpath("Library/Application Support/TechWritersUtilities")

        else:
            prog: str = f"{Path(__file__).parent.name}"
            folder: Path = Path.home().joinpath(".config/TechWritersUtilities")

        return cls(prog, folder)
