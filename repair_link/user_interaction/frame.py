# -*- coding: utf-8 -*-
from tkinter import Misc, IntVar
from tkinter.constants import FLAT
from tkinter.ttk import Frame, Button, Checkbutton
from typing import Iterable, Callable, NamedTuple

from repair_link.user_interaction.const import special_button, pack_special_button, pack_checkbutton


class CheckbuttonPair(NamedTuple):
    # noinspection PyUnresolvedReferences
    """
    The instance to generate values for Checkbuttons.

    Attributes
    ----------
    variable : IntVar
        The variable value of the Checkbutton.
    text : str
        The text value of the Checkbutton.

    """
    variable: IntVar
    text: str

    def __str__(self):
        return f"{self.text} -> {self.variable}"

    __repr__ = __str__


class FrameButtons(Frame):
    """
    The frame with the Ok and Cancel buttons.

    Attributes
    ----------
    master : Misc
        The parent window.

    Methods
    -------
    add_buttons(ok_command, cancel_command)
        Adding Ok and Cancel buttons.

    """

    def __init__(self, master: Misc):
        super().__init__(
            master,
            border=5,
            relief=FLAT,
            padding=(5, 5, 5, 5),
            name="buttons_frame"
        )

    def add_buttons(self, ok_command: Callable, cancel_command: Callable):
        """
        Adding Ok and Cancel buttons.

        Parameters
        ----------
        ok_command : Callable
            The command to invoke pressing the Ok button.
        cancel_command : Callable
            The command to invoke pressing the Cancel button.

        """
        ok_button: Button = special_button(self, ok_command, "ok")
        cancel_button: Button = special_button(self, cancel_command, "cancel")
        pack_special_button(ok_button)
        pack_special_button(cancel_button)


class FrameChoices(Frame):
    """
    The main frame with options.

    Attributes
    ----------
    master : Misc
        The parent window.

    Methods
    -------
    add_checkbuttons(checkbuttons_pairs)
        Adding Checkbutton items.

    """

    def __init__(self, master: Misc):
        super().__init__(
            master,
            border=5,
            relief=FLAT,
            padding=(5, 5, 5, 5),
            name="general_frame")

    def add_checkbuttons(self, checkbutton_pairs: Iterable[CheckbuttonPair]):
        """
        Adding Checkbutton items.

        Parameters
        ----------
        checkbutton_pairs : Iterable[CheckbuttonPair]
            The Checkbutton parameters to use.

        """
        for checkbutton_pair in checkbutton_pairs:
            checkbutton: Checkbutton = Checkbutton(
                self,
                offvalue=0,
                onvalue=1,
                variable=checkbutton_pair.variable,
                text=checkbutton_pair.text
            )
            pack_checkbutton(checkbutton)
