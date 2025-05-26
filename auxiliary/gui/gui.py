# -*- coding: utf-8 -*-
import subprocess
import sys
from tkinter import BooleanVar, filedialog, messagebox, StringVar, Text, Tk, Variable, Widget
from tkinter.constants import BOTH, DISABLED, END, NORMAL, W
from tkinter.ttk import Button, Checkbutton, Entry, Frame, Label, Notebook
from typing import Mapping


class CommandTab:
    """Base class for command tabs with common functionality"""
    name: str

    def __init__(self, master: Tk, tab_name: str, common_vars: Mapping[str, Variable] = None):
        if common_vars is None:
            common_vars: dict[str, Variable] = {}

        else:
            common_vars: dict[str, Variable] = {**common_vars}

        self._master: Tk = master
        self._tab_name: str = tab_name
        self._common_vars: dict[str, Variable] = common_vars
        self._frame: Frame = Frame(self._master)
        self._widgets: dict[str, Variable | Widget | Entry] = {}
        self._row_counter: int = 0

        self.build_tab()
        self.load_command_options()

    def build_tab(self):
        raise NotImplementedError

    def add_file_selector(self, label_text="Выберите файлы:"):
        """Add file selection components"""
        self._add_label(label_text)
        self._widgets["files_entry"] = Entry(
            self._frame, width=50,
            textvariable=self._common_vars["files"])
        self._place_widget(self._widgets["files_entry"])
        self._add_browse_button(lambda: self._browse_files(self._widgets["files_entry"]))

    def add_directory_selector(self, label_text="Выберите директорию"):
        """Add directory selection components"""
        self._add_label(label_text)
        self._widgets["dir_entry"] = Entry(
            self._frame,
            width=50,
            textvariable=self._common_vars["directory"])
        self._place_widget(self._widgets["dir_entry"])
        self._add_browse_button(lambda: self._browse_directory(self._widgets["dir_entry"]))

    def add_checkbox(self, name, label_text, default=False):
        """Add a checkbox component"""
        var: BooleanVar = BooleanVar(value=default)
        self._widgets[f"{name}_var"] = var

        cb = Checkbutton(self._frame, text=label_text, variable=var)
        self._place_widget(cb, columnspan=2)

        return var

    def add_entry(self, name, label_text, default="", width=10):
        """Add labeled entry component"""
        self._add_label(label_text)
        self._widgets[f"{name}_entry"] = Entry(self._frame, width=width)
        self._place_widget(self._widgets[f"{name}_entry"], sticky=W)

        if default:
            self._widgets[f"{name}_entry"].insert(0, default)

        return self._widgets[f"{name}_entry"]

    def add_select_button(self):
        """Add command selection button"""
        btn = Button(
            self._frame, text="Select This Command",
            command=lambda: self._select_command())
        self._place_widget(btn, columnspan=3, pady=10)

    def _add_label(self, text):
        """Add a label widget"""
        label = Label(self._frame, text=text)
        label.grid(row=self._row_counter, column=0, padx=5, pady=5, sticky=W)

    def _place_widget(
            self,
            widget: Widget,
            column: int = 1,
            sticky: str = W,
            columnspan: int = 1,
            padx: int = 10,
            pady: int = 10):
        """Place a widget in the grid"""
        widget.grid(
            row=self._row_counter,
            column=column,
            padx=padx,
            pady=pady,
            sticky=sticky,
            columnspan=columnspan)
        self._row_counter += 1

    def _add_browse_button(self, command):
        """Add browse button"""
        btn: Button = Button(self._frame, text="Browse...", command=command)
        btn.grid(row=self._row_counter - 1, column=2, padx=5, pady=5)

    def _browse_files(self, entry_widget):
        """Handle file browsing"""
        filenames: tuple[str, ...] | str = filedialog.askopenfilenames()

        if filenames:
            entry_widget.delete(0, END)
            entry_widget.insert(0, " ".join(filenames))
            self._common_vars["files"].set(" ".join(filenames))

    def _browse_directory(self, entry_widget):
        """Handle directory browsing"""
        dirname: str = filedialog.askdirectory()

        if dirname:
            entry_widget.delete(0, END)
            entry_widget.insert(0, dirname)
            self._common_vars["directory"].set(dirname)

    def _select_command(self):
        """Select this command for execution"""
        self._master.selected_command = self._tab_name
        messagebox.showinfo(
            "Command Selected",
            f"{self._tab_name.replace("_", " ").title()} command selected for execution.")

    def build_command(self) -> list[str]:
        raise NotImplementedError

    @property
    def frame(self):
        return self._frame


class FormatCodeTab(CommandTab):
    """Tab for format-code command"""
    name: str = "format-code"

    def __init__(self, master: Tk, common_vars: Mapping[str, Variable]):
        super().__init__(master, "format_code", common_vars)
        self.build_tab()

    def build_tab(self):
        self.add_file_selector()
        self.add_directory_selector()

        # Line length
        self.add_entry("length", "Max Line Length:", "120")

        # Checkboxes
        self.add_checkbox("recursive", "Recursive", self._common_vars["recursive"].get())
        self.add_checkbox("keep_logs", "Keep Logs", self._common_vars["keep_logs"].get())

        self.add_select_button()

    def build_command(self) -> list[str]:
        """Build the Click command from GUI inputs"""
        command: list[str] = ["format-code"]

        # Files
        if files := self._widgets["files_entry"].get():
            command.extend(["-f", *files.split()])

        # Directory
        if directory := self._widgets["dir_entry"].get():
            command.extend(["-d", directory])

        # Line length
        if length := self._widgets["length_entry"].get():
            command.extend(["-l", length])

        # Flags
        if not self._widgets["recursive_var"].get():
            command.append("-R")
        if self._widgets["keep_logs_var"].get():
            command.append("-k")

        return command


class ListFilesTab(CommandTab):
    """Tab for list-files command"""
    name: str = "list-files"

    def __init__(self, master, common_vars):
        super().__init__(master, "list_files", common_vars)
        self.build_tab()

    def build_tab(self):
        # Root directory (uses common directory)
        self._add_label("Root Directory:")
        self._widgets["root_dir_entry"] = Entry(
            self._frame, width=50,
            textvariable=self._common_vars["directory"])
        self._place_widget(self._widgets["root_dir_entry"])
        self._add_browse_button(lambda: self._browse_directory(self._widgets["root_dir_entry"]))

        # Ignored directories
        self.add_entry("ignored_dirs", "Ignored Directories:", "_temp_folder, _temp_storage, private", 50)

        # Checkboxes
        self.add_checkbox("all_dirs", "Process All Directories")
        self.add_checkbox("all_files", "Process All Files")
        self.add_checkbox("all_extensions", "Process All Extensions")
        self.add_checkbox("all_languages", "Process All Languages", True)
        self.add_checkbox("ignore_index", "Ignore Index Files")
        self.add_checkbox("no_prefix", "No Prefix")
        self.add_checkbox("hidden", "Include Hidden Files")

        # Additional entries
        self.add_entry("ignored_files", "Ignored Files:", "README, _check_list", 50)
        self.add_entry("extensions", "Extensions:", "md adoc", 50)
        self.add_entry("language", "Language:", width=20)
        self.add_entry("prefix", "Prefix:", width=50)

        # Common checkboxes
        self.add_checkbox("recursive", "Recursive", self._common_vars["recursive"].get())
        self.add_checkbox("keep_logs", "Keep Logs", self._common_vars["keep_logs"].get())

        self.add_select_button()

    def build_command(self) -> list[str]:
        """Build the Click command from GUI inputs"""
        command: list[str] = ["list-files"]

        # Root directory (required)
        if not (root_dir := self._widgets["root_dir_entry"].get()):
            raise ValueError("Root directory is required")

        command.append(root_dir)

        # Directories options
        if self._widgets["all_dirs_var"].get():
            command.append("--all-dirs")

        elif ignored_dirs := self._widgets["ignored_dirs_entry"].get():
            command.extend(["-d", *ignored_dirs.split(",")])

        # Files options
        if self._widgets["all_files_var"].get():
            command.append("--all-files")

        elif ignored_files := self._widgets["ignored_files_entry"].get():
            command.extend(["-f", *ignored_files.split(",")])

        # Extensions
        if self._widgets["all_extensions_var"].get():
            command.append("--all-ext")

        elif extensions := self._widgets["extensions_entry"].get():
            command.extend(["-e", extensions])

        # Language
        if self._widgets["all_languages_var"].get():
            command.append("--all-langs")

        elif language := self._widgets["language_entry"].get():
            command.extend(["-l", language])

        # Other options
        if self._widgets["ignore_index_var"].get():
            command.append("-i")

        if self._widgets["no_prefix_var"].get():
            command.append("-n")

        elif prefix := self._widgets["prefix_entry"].get():
            command.extend(["-p", prefix])

        if self._widgets["hidden_var"].get():
            command.append("-H")

        if not self._widgets["recursive_var"].get():
            command.append("-R")

        if self._widgets["keep_logs_var"].get():
            command.append("-k")

        return command


class RepairSvgTab(CommandTab):
    """Tab for repair-svg command"""
    name: str = "repair-svg"

    def __init__(self, master, common_vars):
        super().__init__(master, "repair_svg", common_vars)
        self.build_tab()

    def build_tab(self):
        self.add_file_selector()
        self.add_directory_selector()

        # Checkboxes
        self.add_checkbox("recursive", "Recursive", self._common_vars["recursive"].get())
        self.add_checkbox("keep_logs", "Keep Logs", self._common_vars["keep_logs"].get())

        self.add_select_button()

    def build_command(self) -> list[str]:
        """Build the Click command from GUI inputs"""
        command = ["repair-svg"]

        # Files
        if files := self._widgets["files_entry"].get():
            command.extend(["-f", *files.split()])

        # Directory
        if directory := self._widgets["dir_entry"].get():
            command.extend(["-d", directory])

        # Flags
        if not self._widgets["recursive_var"].get():
            command.append("-R")

        if self._widgets["keep_logs_var"].get():
            command.append("-k")

        return command


# noinspection PyTypeChecker
class CommandGUI:
    def __init__(self, root):
        self._root: Tk = root
        self._root.title("Command GUI")

        # Common variables shared across tabs
        self._common_vars = {
            "files": StringVar(),
            "directory": StringVar(),
            "recursive": BooleanVar(value=True),
            "keep_logs": BooleanVar(value=False)
        }

        # Create notebook
        self._notebook: Notebook = Notebook(root)
        self._notebook.pack(fill=BOTH, expand=True)

        # Create tabs
        self._tabs: dict[str, CommandTab] = {
            "format_code": FormatCodeTab(self._notebook, self._common_vars),
            "list_files": ListFilesTab(self._notebook, self._common_vars),
            "repair_svg": RepairSvgTab(self._notebook, self._common_vars)
        }

        # Add tabs to notebook
        for name, tab in self._tabs.items():
            self._notebook.add(tab.frame, text=name.replace("_", " ").title())

        # Execute button
        self.execute_button: Button = Button(
            root,
            text="Execute Command",
            command=self.execute_command
        )
        self.execute_button.pack(pady=10)

        # Selected command
        self.selected_command: str = None

        # Output console
        self.console: Text = Text(root, height=10, state=DISABLED)
        self.console.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Add clear button
        Button(
            root,
            text="Clear Console",
            command=self.clear_console
        ).pack(pady=5)

    def clear_console(self):
        """Clear the console output"""
        self.console.config(state=NORMAL)
        self.console.delete(1.0, END)
        self.console.config(state=DISABLED)

    def log_output(self, text: str):
        """Log text to the console"""
        self.console.config(state=NORMAL)
        self.console.insert(END, text + "\n")
        self.console.see(END)
        self.console.config(state=DISABLED)

    def execute_command(self):
        """Execute the selected command"""
        if not self.selected_command:
            messagebox.showerror("Error", "No command selected. Please select a command first.")
            return

        try:
            tab: CommandTab = self._tabs[self.selected_command]
            command = tab.build_command()

            # Convert to string for display
            cmd_str = " ".join(command)
            self.log_output(f"Executing: {cmd_str}")

            # Execute the command
            result = subprocess.run(
                [sys.executable, "-m", "your_module"] + command,
                capture_output=True,
                text=True
            )

            # Display output
            if result.stdout:
                self.log_output(result.stdout)

            if result.stderr:
                self.log_output(f"Error: {result.stderr}")

            self.log_output(f"Command completed with return code: {result.returncode}")

        except ValueError as e:
            messagebox.showerror("Input Error", str(e))

        except Exception as e:
            messagebox.showerror("Execution Error", f"Failed to execute command: {str(e)}")


if __name__ == "__main__":
    root = Tk()
    app = CommandGUI(root)
    root.mainloop()
