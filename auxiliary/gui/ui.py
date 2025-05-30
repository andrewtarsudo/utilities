# -*- coding: utf-8 -*-
from functools import wraps
from pathlib import Path
from typing import Callable, Iterable

from click.core import Command, Context, Group
from click.decorators import command, pass_context
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Input, Label, Static
from trogon import tui

from utilities.common.shared import StrPath


class TreeElementSelector(ModalScreen[str | None]):
    """A modal file/directory selector dialog that works with any Textual app."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+c", "cancel", "Cancel"),
        Binding("enter", "select", "Select"),
        Binding("ctrl+h", "toggle_hidden", "Toggle Hidden Files"),
    ]

    CSS = """
    TreeElementSelector {
        align: center middle;
    }

    #dialog {
        width: 80%;
        height: 70%;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }

    #title {
        text-align: center;
        margin-bottom: 1;
        text-style: bold;
        color: $primary;
    }

    #tree {
        height: 1fr;
        border: solid $primary-lighten-1;
        margin-bottom: 1;
    }

    #current_selection {
        height: 1;
        margin-bottom: 1;
        color: $accent;
        text-style: italic;
    }

    #input_row {
        height: 3;
        margin-bottom: 1;
    }

    #manual_input {
        width: 1fr;
    }

    #buttons {
        height: 3;
        align: center middle;
    }

    #buttons Button {
        margin: 0 1;
        min-width: 10;
    }
    """

    def __init__(
            self,
            title: str = "Выберите файл",
            file_mode: bool = True,
            existing_only: bool = False,
            initial_path: StrPath | None = None,
            file_extensions: Iterable[str] | None = None,
            show_hidden: bool = True):
        if file_extensions is None:
            file_extensions: list[str] = []

        else:
            file_extensions: list[str] = list(map(lambda x: x.lower(), file_extensions))

        if initial_path is None:
            initial_path: Path = Path.home()

        else:
            initial_path: Path = Path(initial_path)

        super().__init__()

        self._title: str = title
        self._file_mode: bool = file_mode
        self._existing_only: bool = existing_only
        self._file_extensions: list[str] = file_extensions
        self._initial_path: Path = initial_path
        self._selected_path: reactive[str] = reactive("")
        self._show_hidden: bool = show_hidden

    def compose(self) -> ComposeResult:
        """Compose the file selector interface."""
        with Vertical(id="dialog"):
            yield Static(self._title, id="title")
            yield DirectoryTree(self._initial_path, id="tree")
            yield Label("", id="current_selection")

            with Horizontal(id="input_row"):
                yield Input(
                    placeholder="Or type path manually...",
                    id="manual_input",
                    value=self._initial_path.as_posix())

            with Horizontal(id="buttons"):
                yield Button("Select", id="select", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        """Set focus to the directory tree when mounted."""
        tree: DirectoryTree = self.query_one(DirectoryTree)
        tree.focus()
        self._update_selection_display()

    def on_file_selected(self, event) -> None:
        """Handle file selection from tree."""
        path_str = str(event.path)

        # Check file extension if specified
        if self._file_extensions and self._file_mode:
            path_obj: Path = Path(path_str)

            if path_obj.suffix.lower() not in self._file_extensions:
                self.show_message(f"Please select a file with extension: {', '.join(self._file_extensions)}")
                return

        self._selected_path = path_str
        self._update_selection_display()

        if self._file_mode:
            # Auto-dismiss on file selection if in file mode
            self.dismiss(path_str)

    def on_directory_selected(self, event) -> None:
        """Handle directory selection from tree."""
        path_str = str(event.path)
        self._selected_path = path_str
        self._update_selection_display()

        if not self._file_mode:
            # Auto-dismiss on directory selection if in directory mode
            self.dismiss(path_str)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "select":
            self.action_select()

        elif event.button.id == "cancel":
            self.action_cancel()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle enter key in manual input."""
        if event.input.id == "manual_input":
            self.action_select()

    def action_select(self) -> None:
        """Select the current path."""
        # Try manual input first
        manual_input: Input = self.query_one("#manual_input", Input)

        if manual_input.value.strip():
            path: Path = Path(manual_input.value.strip()).expanduser().resolve()

            if self._validate_path(path):
                self.dismiss(str(path))
                return

        selected: str = f"{self._selected_path!s}"

        # Otherwise use tree selection
        if self._selected_path:
            path: Path = Path(selected)

            if self._validate_path(path):
                self.dismiss(selected)
                return

        # Try tree cursor
        tree: DirectoryTree = self.query_one(DirectoryTree)

        if tree.cursor_node and hasattr(tree.cursor_node, "data") and tree.cursor_node.data is not None:
            path: Path = tree.cursor_node.data.path

            if self._validate_path(path):
                self.dismiss(str(path))
                return

        # Show error if no valid selection
        self.show_message("Please select a valid path or enter one manually")

    def action_cancel(self) -> None:
        """Cancel the selection."""
        self.dismiss()

    def action_toggle_hidden(self) -> None:
        """Toggle display of hidden files."""
        self._show_hidden = not self._show_hidden
        tree: DirectoryTree = self.query_one(DirectoryTree)
        tree.show_hidden = self._show_hidden
        tree.reload()

    def _validate_path(self, path: Path) -> bool:
        """Validate the selected path based on mode and requirements."""
        fm: bool = self._file_mode
        ex: bool = path.exists()
        f: bool = path.is_file()
        d: bool = path.is_dir()

        if self._existing_only and not ex:
            self.show_message(f"Путь {path.as_posix()} не найден")
            return False

        elif fm and ex and not f:
            if d:
                self.show_message("Выберите файл, а не директорию")
                return False

        elif not fm and ex and not d:
            self.show_message("Выберите директорию, а не файл")
            return False

        # Check file extensions
        elif self._file_extensions and fm and ex and f:
            if path.suffix.lower() not in self._file_extensions:
                _: str = ", ".join(self._file_extensions)
                self.show_message(f"У файла должно быть расширение из {_}")
                return False

        else:
            return True

    def _update_selection_display(self):
        """Update the current selection display."""
        if self._selected_path:
            self.query_one("#current_selection", Label).update(f"{self._selected_path!s}")

        else:
            self.query_one("#current_selection", Label).update("")

    def show_message(self, message: str):
        """Show a message in the selection display."""
        self.query_one("#current_selection", Label).update(message)


# class FileBrowserApp(App):
#     """Standalone file browser application."""
#
#     def __init__(self, **selector_kwargs):
#         super().__init__()
#         self.selector_kwargs: dict[str, Any] = selector_kwargs
#         self.result = None
#
#     def compose(self) -> ComposeResult:
#         yield TreeElementSelector(**self.selector_kwargs)
#
#     def on_file_selector_dismissed(self, event) -> None:
#         """Handle when file selector is dismissed."""
#         self.result = event.result
#         self.exit(event.result)


class CommandTUI(App):
    """Generic TUI for commands with file/directory selection."""

    CSS = """
    #selector-buttons {
        layout: horizontal;
        align: center middle;
        height: 5;
    }
    #selector-buttons Button {
        margin: 1 2;
        min-width: 20;
    }
    #selected-paths {
        border: round $primary;
        padding: 1;
        height: 1fr;
    }
    #command-options {
        border: round $secondary;
        padding: 1;
        height: 1fr;
    }
    """

    def __init__(self, ctx: Context, command: Command):
        super().__init__()
        self.ctx = ctx
        self.command = command
        self.selected_files: list[str] | reactive[list[str]] = reactive([])
        self.selected_dir: str | None | reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        """Compose the TUI interface."""
        yield Label(f"{self.command.name}", id="title")

        # File/Directory selection buttons
        with Horizontal(id="selector-buttons"):
            if any(p.name in ['files', 'file'] for p in self.command.params):
                yield Button("Select Files", id="select-files")
            if any(p.name in ['directory', 'dir'] for p in self.command.params):
                yield Button("Select Directory", id="select-dir")

        # Selected paths display
        yield Label("Selected Paths:", classes="label")
        yield Static("No paths selected yet", id="selected-paths")

        # Command options display
        yield Label("Command Options:", classes="label")
        options_text = "\n".join(
            f"{param.name}: {self.ctx.params.get(param.name, param.default)}"
            for param in self.command.params
            if param.name not in ['files', 'file', 'directory', 'dir', 'help']
        )
        yield Static(options_text or "No additional options", id="command-options")

        # Action buttons
        with Horizontal(id="action-buttons"):
            yield Button("Run Command", id="run", variant="primary")
            yield Button("Cancel", id="cancel")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "select-files":
            await self._select_files()
        elif event.button.id == "select-dir":
            await self._select_directory()
        elif event.button.id == "run":
            self._run_command()
        elif event.button.id == "cancel":
            self.exit(None)

    async def _select_files(self) -> None:
        """Launch file selector."""

        def handle_result(result: str | None) -> None:
            if result:
                self.selected_files.append(result)
                self._update_display()

        # Get file extensions from command if specified
        extensions = []
        if hasattr(self.command, 'extensions'):
            extensions = self.command.extensions
        elif 'extensions' in self.ctx.params:
            extensions = self.ctx.params['extensions']

        selector = TreeElementSelector(
            title=f"Select Files for {self.command.name}",
            file_mode=True,
            existing_only=True,
            file_extensions=extensions
        )
        await self.push_screen(selector, handle_result)

    async def _select_directory(self) -> None:
        """Launch directory selector."""

        def handle_result(result: str | None) -> None:
            if result:
                self.selected_dir = result
                self._update_display()

        selector = TreeElementSelector(
            title=f"Select Directory for {self.command.name}",
            file_mode=False,
            existing_only=True
        )
        await self.push_screen(selector, handle_result)

    def _update_display(self) -> None:
        """Update the display of selected paths."""
        paths_display = self.query_one("#selected-paths", Static)
        paths = []

        if self.selected_files:
            paths.extend(f"• File: {f}" for f in self.selected_files)
        if self.selected_dir:
            paths.append(f"• Directory: {self.selected_dir}")

        paths_display.update("\n".join(paths) if paths else "No paths selected yet")

    def _run_command(self) -> None:
        """Prepare context and exit with success."""
        # Update context with selected values
        if self.selected_files:
            self.ctx.params['files'] = self.selected_files
        if self.selected_dir:
            self.ctx.params['directory'] = self.selected_dir

        self.exit(True)


def with_interactive_selection(command_func: Callable) -> Callable:
    """
    Decorator that adds interactive file/directory selection to a Click command.

    Automatically detects if the command has files/directory options and
    adds TUI support when running interactively.
    """

    @wraps(command_func)
    @pass_context
    def wrapper(ctx: Context, *args, **kwargs):
        # Check if we're running in interactive mode
        if getattr(ctx, "interactive", False):
            # Create and run the TUI
            app = CommandTUI(ctx, ctx.command)
            success = app.run()

            if not success:
                return  # User cancelled

            # The TUI has updated ctx.params with selected values

        # Proceed with original command execution
        return command_func(ctx, *args, **kwargs)

    return wrapper


def add_tui_to_commands(cli_group: Group) -> Group:
    """
    Add interactive TUI support to all commands in a Click group that have
    file/directory options.

    Usage:
        cli = add_tui_to_commands(cli)
    """
    for name, cmd in cli_group.commands.items():
        # Check if command has file/directory options
        has_file_opt = any(p.name in ['files', 'file'] for p in cmd.params)
        has_dir_opt = any(p.name in ['directory', 'dir'] for p in cmd.params)

        if has_file_opt or has_dir_opt:
            # Apply our decorator
            cmd.callback = with_interactive_selection(cmd.callback)

            # Add TUI decorator if not already present
            if not any(d.decorator == tui for d in cmd.__dict__.get('__click_params__', [])):
                cmd = tui(name=cmd.name, help=f"Interactive {cmd.name}")(cmd)

    return cli_group
