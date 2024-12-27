# -*- coding: utf-8 -*-
from sys import platform
from tkinter import IntVar, Tk
from tkinter.font import Font
from tkinter.ttk import Style
from typing import Iterator

from loguru import logger

from repair_link.user_interaction.const import InputUser, root_title, titles, get_pathdir, _width_app, _height_app
from repair_link.user_interaction.frame import CheckbuttonPair, FrameChoices, FrameButtons


class App:
    """
    The application to generate the GUI.

    Attributes
    ----------
    _root : Tk
        The root window.
    _input_user : InputUser
        The user choices.
    _dry_run_int_var : IntVar
        The variable to get --dry-run option.
    _keep_log_int_var : IntVar
        The variable to get --keep-log option.
    _anchor_validation_int_var : IntVar
        The variable to get --anchor-
    _no_result_int_var : IntVar
        The variable to get --no-result option.

    """

    def __init__(self, root: Tk):
        self._root: Tk = root
        self._root.geometry(f"{_width_app}x{_height_app}")

        self._input_user: InputUser | None = None
        self._dry_run_int_var: IntVar = IntVar(value=1, name="dry_run")
        self._keep_log_int_var: IntVar = IntVar(value=0, name="keep_log")
        self._anchor_validation_int_var: IntVar = IntVar(value=1, name="anchor_validation")
        self._no_result_int_var: IntVar = IntVar(value=1, name="no_result")
        self._separate_int_var: IntVar = IntVar(value=1, name="separate")
        self._skip_en_int_var: IntVar = IntVar(value=1, name="skip_en")

        if platform.startswith("win"):
            self._root.attributes('-toolwindow', True)

    def _add_styles(self):
        """
        Adding custom styles.

        """
        s: Style = Style(self._root)

        _button_font: Font = Font(
            family="Times",
            name="TButton",
            size=12,
            weight="normal",
            slant="roman",
            underline=False,
            overstrike=False)
        s.configure("TButton", font=_button_font)

    def _center(self):
        """
        Centering the root window.

        """
        w: int = _width_app
        h: int = _height_app
        _shift_x: int = (self._root.winfo_screenwidth() - w) // 2
        _shift_y: int = (self._root.winfo_screenheight() - h) // 2
        self._root.wm_geometry(f"{w}x{h}+{_shift_x}+{_shift_y}")

    def _prepare(self):
        """
        Applying pre-actions.

        """
        self._root.bind("<Escape>", self.cancel)
        self._root.wm_title(root_title)
        self._root.wm_resizable(False, False)
        self._root.wm_withdraw()

    def _int_vars(self) -> Iterator[IntVar]:
        """
        The iteration of the IntVar values.

        Returns
        -------
        Iterator[IntVar]

        """
        return iter(
            (self._dry_run_int_var,
             self._keep_log_int_var,
             self._no_result_int_var,
             self._anchor_validation_int_var,
             self._separate_int_var,
             self._skip_en_int_var)
        )

    @property
    def _checkbutton_pairs(self) -> Iterator[CheckbuttonPair]:
        """
        The iteration of the CheckbuttonPair values.

        Returns
        -------
        Iterator[CheckbuttonPair]

        """
        return iter(
            CheckbuttonPair(int_var, text)
            for int_var, text in zip(self._int_vars(), titles))

    def _get_options(self, pathdir: str | None):
        """
        The generation of the main frame.

        Parameters
        ----------
        pathdir : str or None
            The path to the directory to process files.

        """

        def ok_command():
            self._input_user = InputUser(
                pathdir,
                not bool(self._dry_run_int_var.get()),
                bool(self._keep_log_int_var.get()),
                bool(self._no_result_int_var.get()),
                bool(self._anchor_validation_int_var.get()),
                bool(self._separate_int_var.get()),
                bool(self._skip_en_int_var.get()))
            self._root.destroy()

        def cancel_command():
            logger.critical(f"Выбор отменен пользователем")
            self._root.destroy()

        frame_choices: FrameChoices = FrameChoices(self._root)
        frame_choices.add_checkbuttons(self._checkbutton_pairs)

        frame_buttons: FrameButtons = FrameButtons(frame_choices)
        frame_buttons.add_buttons(ok_command, cancel_command)

        frame_buttons.pack()
        frame_choices.pack()

    def run(self):
        """
        The main generation process.

        """
        self._prepare()
        self._center()
        self._add_styles()
        pathdir: str | None = get_pathdir()

        if not isinstance(pathdir, str) or not pathdir:
            self.cancel()
            return

        self._root.wm_deiconify()
        self._get_options(pathdir)

    @property
    def root(self):
        return self._root

    @property
    def input_user(self):
        return self._input_user

    # noinspection PyUnusedLocal
    def cancel(self, event=None):
        """
        The action invoked by the X button.

        """
        logger.critical(f"Выбор отменен пользователем")
        self._root.destroy()
