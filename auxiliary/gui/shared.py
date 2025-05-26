# -*- coding: utf-8 -*-
from functools import partial
from tkinter import BooleanVar, Canvas, Checkbutton, Entry, filedialog, Frame, Label, Listbox, messagebox, \
    Radiobutton, Scrollbar, StringVar, Tk
from tkinter.constants import BOTH, END, LEFT, NW, RIGHT, VERTICAL, W, X, Y
from tkinter.ttk import Button, Combobox, LabelFrame
from typing import Any, Dict, List, Literal, Optional, Tuple, TypeAlias, Union

from utilities.common.config_file import config_file

# Type aliases
WidgetType: TypeAlias = Union[Entry, BooleanVar, Listbox, StringVar]
FileDialogResult: TypeAlias = Union[Tuple[str, ...], Literal[""]]


def browse_file(entry: Entry) -> None:
    path: str = filedialog.askopenfilename(title="Select a file")
    if path:
        entry.delete(0, END)
        entry.insert(0, path)


def browse_dir(entry: Entry) -> None:
    path: str = filedialog.askdirectory(title="Select a directory")
    if path:
        entry.delete(0, END)
        entry.insert(0, path)


def add_to_listbox(listbox: Listbox, entry: Entry) -> None:
    val: str = entry.get().strip()
    if val:
        listbox.insert(END, val)
        entry.delete(0, END)


def browse_files(listbox: Listbox) -> None:
    paths: FileDialogResult = filedialog.askopenfilenames(title="Select files")
    if paths:  # Check if user didn't cancel
        for p in paths:
            if p not in listbox.get(0, END):
                listbox.insert(END, p)


def create_listbox(parent: Frame, key: str, default: List[str], is_files: bool) -> Tuple[Frame, Listbox]:
    row: Frame = Frame(parent)
    row.pack(fill=X, pady=5, anchor=W)
    Label(row, text=key, width=20, anchor=W).pack(side=LEFT)

    listbox: Listbox = Listbox(row, height=1)
    listbox.pack(side=LEFT, fill=X, expand=True)
    for item in default:
        listbox.insert(END, item)

    add_entry: Entry = Entry(row)
    add_entry.pack(side=LEFT, padx=(5, 0))
    Button(
        row,
        text="Добавить +",
        command=partial(add_to_listbox, listbox, add_entry)
    ).pack(side=LEFT, padx=(5, 10))

    if is_files:
        Button(
            row,
            text="Выбрать файлы",
            command=partial(browse_files, listbox)
        ).pack(side=LEFT, padx=(0, 10))

    return row, listbox


def create_checkbox(parent: Frame, key: str, default: bool) -> Tuple[Frame, BooleanVar]:
    row: Frame = Frame(parent)
    row.pack(fill=X, pady=5, anchor=W)
    Label(row, text=key, width=20, anchor=W).pack(side=LEFT)
    var: BooleanVar = BooleanVar(value=default)
    Checkbutton(row, variable=var).pack(side=LEFT)
    return row, var


def create_entry(parent: Frame, key: str, default: str, is_files: bool, is_dir: bool) -> Tuple[Frame, Entry]:
    row: Frame = Frame(parent)
    row.pack(fill=X, pady=5, anchor=W)
    Label(row, text=key, width=20, anchor=W).pack(side=LEFT)

    entry: Entry = Entry(row)
    entry.insert(0, default)
    entry.pack(side=LEFT, fill=X, expand=True)

    if is_files:
        (Button(
            row,
            text="Выбрать файл",
            command=partial(browse_file, entry))
         .pack(side=LEFT, padx=(5, 10)))

    elif is_dir:
        (Button(
            row,
            text="Выбрать директорию",
            command=partial(browse_dir, entry))
         .pack(side=LEFT, padx=(5, 10)))

    return row, entry


class ClickGUI(Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Click Command GUI")
        self.geometry("1000x700")
        self.config(padx=20, pady=20)

        # Data structures with type hints
        self.commands: List[str] = ["format-code", "list-files", "repair-svg"]
        self.command_forms: Dict[str, Frame] = {}  # Stores all command forms
        self.option_widgets: Dict[str, Dict[str, WidgetType]] = {}  # Widgets by command
        self.saved_values: Dict[str, Dict[str, Any]] = {}  # Saved values by command
        self.current_command: str = ""
        self.current_form: Optional[Frame] = None

        # UI elements with type hints
        self.lang_var: StringVar
        self.command_var: StringVar
        self.canvas: Canvas
        self.scrollbar: Scrollbar
        self.forms_container: Frame

        # Setup UI
        self._create_language_selector()
        self._create_command_selector()
        self._create_scrollable_area()
        self._create_run_button()

        # Pre-generate all command forms
        self._initialize_command_forms()

    def _create_language_selector(self) -> None:
        lang_frame: Frame = Frame(self)
        lang_frame.pack(anchor=W, pady=(0, 10))
        Label(lang_frame, text="Language:", font=("Arial", 10)).pack(side=LEFT)
        self.lang_var = StringVar(value="ru")
        (Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=["ru", "en", "fr"],
            state="readonly",
            width=5)
         .pack(side=LEFT, padx=(5, 0)))

    def _create_command_selector(self) -> None:
        Label(self, text="Select Command:", font=("Arial", 12, "bold")).pack(anchor=W)
        self.command_var = StringVar(value=self.commands[0])
        combo: Combobox = Combobox(
            self,
            textvariable=self.command_var,
            values=self.commands,
            state="readonly")
        combo.pack(fill=X, pady=(0, 10))
        combo.bind("<<ComboboxSelected>>", self._on_command_change)

    def _create_scrollable_area(self) -> None:
        container: Frame = Frame(self)
        container.pack(fill=BOTH, expand=True)

        self.canvas = Canvas(container, borderwidth=0)
        self.scrollbar = Scrollbar(container, orient=VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.forms_container = Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.forms_container, anchor=NW)

        self.forms_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

    def _create_run_button(self) -> None:
        (Button(
            self,
            text="Run Command",
            command=self._run_command)
         .pack(pady=(10, 0)))

    def _initialize_command_forms(self) -> None:
        for command in self.commands:
            form_frame: Frame = Frame(self.forms_container)
            self.command_forms[command] = form_frame
            self.option_widgets[command] = {}
            self._create_command_form(command, form_frame)
            form_frame.pack_forget()

        self.current_command = self.commands[0]
        self.command_forms[self.current_command].pack(fill=BOTH, expand=True)

    def _create_command_form(self, command: str, parent: Frame) -> None:
        opts: Dict[str, Any] = config_file.get_commands(command)
        self.saved_values[command] = {}

        checkbox_frame: Frame = Frame(parent)
        checkbox_frame.pack(fill=X, pady=5, anchor=W)
        checkbox_columns: List[Frame] = [Frame(checkbox_frame) for _ in range(3)]
        for col in checkbox_columns:
            col.pack(side=LEFT, expand=True, fill=BOTH, padx=5)

        checkbox_count: int = 0

        for key, val in opts.items():
            is_checkbox: bool = isinstance(val, bool)
            is_files: bool = "file" in key.lower() or "files" in key.lower()
            is_dir: bool = "dir" in key.lower() or "directory" in key.lower()

            if is_checkbox:
                column_index: int = checkbox_count % 3
                target_frame: Frame = checkbox_columns[column_index]
                checkbox_count += 1
                row, widget = create_checkbox(target_frame, key, val)

            elif isinstance(val, list):
                row, widget = create_listbox(parent, key, val, is_files)

            elif isinstance(val, (int, str)):
                row, widget = create_entry(parent, key, str(val), is_files, is_dir)

            else:
                continue

            self.option_widgets[command][key] = widget

        if command == "list-files":
            self._add_radiobutton_group(
                parent,
                command,
                "Directories Option",
                "dirs_group",
                [("Use Ignored Dirs", "ignored_dirs"), ("Use All Dirs", "all_dirs")])

    def _add_radiobutton_group(
            self,
            parent: Frame,
            command: str,
            label: str,
            varname: str,
            options: list[tuple[str, str]]) -> None:
        frame: LabelFrame = LabelFrame(parent, text=label, padding=10)
        frame.pack(fill=X, pady=10)

        var: StringVar = StringVar(value=options[0][1])
        for text, value in options:
            Radiobutton(frame, text=text, variable=var, value=value).pack(anchor=W)

        self.option_widgets[command][varname] = var

    def _on_command_change(self, event: Any) -> None:
        if self.current_command:
            self._save_current_values()

        self.command_forms[self.current_command].pack_forget()

        self.current_command = self.command_var.get()
        self.command_forms[self.current_command].pack(fill=BOTH, expand=True)

        self.canvas.yview_moveto(0)

    def _save_current_values(self) -> None:
        command: str = self.current_command
        self.saved_values[command] = {}

        for key, widget in self.option_widgets[command].items():
            if isinstance(widget, (Entry, BooleanVar, StringVar)):
                self.saved_values[command][key] = widget.get()
            elif isinstance(widget, Listbox):
                self.saved_values[command][key] = [widget.get(i) for i in range(widget.size())]

    def _run_command(self) -> None:
        self._save_current_values()

        command: str = self.current_command
        language: str = self.lang_var.get()
        options: Dict[str, Any] = self.saved_values.get(command, {})

        messagebox.showinfo(
            "Command Execution",
            f"Would run: {command}\nLanguage: {language}\nOptions:\n{options}"
        )


if __name__ == "__main__":
    app: ClickGUI = ClickGUI()
    app.mainloop()
