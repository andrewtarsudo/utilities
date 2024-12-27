# -*- coding: utf-8 -*-
from tkinter import Tk

from repair_link.general.custom_logger import configure_custom_logging
from repair_link.user_interaction.app import App
from repair_link.user_interaction.const import InputUser


@configure_custom_logging("link_repair", is_initial=False)
def get_input_user() -> InputUser | None:
    """
    Getting the user input and converting to the FileItem instances.

    Returns
    -------
    list[FileItem] | None
        The FileItem objects if not aborted.

    """
    root: Tk = Tk()
    app: App = App(root)
    app.run()
    app.root.mainloop()
    input_user: InputUser = app.input_user

    return input_user
