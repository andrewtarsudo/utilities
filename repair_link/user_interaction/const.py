# -*- coding: utf-8 -*-
from locale import getlocale
from pathlib import Path
from tkinter.constants import W, LEFT
from tkinter.filedialog import askdirectory
from tkinter.ttk import Frame, Button, Checkbutton
from typing import Callable, TypeAlias, NamedTuple

from loguru import logger

from repair_link.general.const import prepare_logging

# ---------- GUI constants ---------- #
root_title: str = "Исправление ссылок"
ask_directory_title: str = "Выбрать директорию для обработки:"

dry_run_title: str = "Изменить файлы в директории"
keep_log_title: str = "Сохранить лог-файл"
no_result_title: str = "Сохранить файл с изменениями, result.txt"
anchor_validation_title: str = "Проверить якори внутри файлов"
separate_languages_title: str = "Обработать файлы на русском и английском отдельно"
skip_en_title: str = "Пропустить файлы на английском"
titles: tuple[str, ...] = (
    dry_run_title,
    keep_log_title,
    no_result_title,
    anchor_validation_title,
    separate_languages_title,
    skip_en_title)
names: dict[str, str] = {
    "ok": "Ok",
    "cancel": "Отмена"
}

if getlocale()[0] == "en_US":
    PRESS_ENTER_KEY: str = "\nPress the ENTER key to stop the script ..."

else:
    PRESS_ENTER_KEY: str = "\nНажмите ENTER, чтобы завершить работу скрипта ..."
# ---------- GUI constants ---------- #

TriState: TypeAlias = bool | None

_width_app: int = 450
_height_app: int = 360


def find_initial_dir() -> Path:
    """
    The search of the possible initial directory.

    Returns
    -------
    Path
        The existing directory from the number of possible ones.

    """
    _dirs: tuple[str, ...] = ("PycharmProjects", "IdeaProjects")

    for _dir in _dirs:
        _: Path = Path.home().joinpath(_dir)

        if _.exists():
            logger.debug(f"initial dir = {_}")
            return _

    else:
        logger.debug("initial dir = default")
        return Path.home().joinpath("Desktop")


def null_command():
    """
    The command for radiobuttons and checkbuttons.

    """
    pass


def special_button(frame: Frame, command: Callable, name: str):
    """
    The generation of the specialized button.

    Parameters
    ----------
    frame : Frame
        The frame to add the button.
    command : Callable
        The command to invoke.
    name : str
        The internal name in the root window.

    Returns
    -------
    Button
        The custom button, Ok or Cancel.

    """
    return Button(
        frame,
        command=command,
        default="normal",
        name=name,
        style="TButton",
        text=names.get(name),
        padding=[5, 5, 5, 5])


def pack_special_button(button: Button):
    """
    Packing the button into the frame.

    Parameters
    ----------
    button : Button
        The Button to pack.

    """
    button.pack(padx=20, pady=20, anchor=W, side=LEFT)


def pack_checkbutton(checkbutton: Checkbutton):
    """
    Packing the checkbutton into the frame.

    Parameters
    ----------
    checkbutton : Checkbutton
        The Checkbutton to pack.

    """
    checkbutton.pack(anchor=W, ipadx=10, ipady=10)


def get_pathdir() -> str:
    """
    The generation of the askdirectory dialog box.

    Returns
    -------
    str
        The directory path.

    """
    return askdirectory(
        initialdir=find_initial_dir(),
        mustexist=True,
        title=ask_directory_title)


class InputUser(NamedTuple):
    # noinspection PyUnresolvedReferences
    """
    The user input values.

    Attributes
    ----------
    pathdir : str
        The path to the directory.
    dry_run : bool
        The flag not to modify files.
    keep_log : bool
        The flag to store the log file.
    no_result : bool
        The flag to remove the file with modifications.
    anchor_validation : bool
        The flag to validate anchors in the text files.
    separate_languages : bool
        The flag to process files separately according to their languages.
    skip_en : bool
        The flag to ignore English files.

    """
    pathdir: str | None
    dry_run: bool
    keep_log: bool
    no_result: bool
    anchor_validation: bool
    separate_languages: bool
    skip_en: bool

    def __str__(self):
        return prepare_logging((f"{k}={v}" for k, v in self._asdict().items()), "")

    def __repr__(self):
        return f"<{self.__class__.__name__}(\n{self._asdict()}\n)>"

    def __bool__(self):
        return self.pathdir is not None
