# -*- coding: utf-8 -*-
from pathlib import Path

from click.core import Group
from click.decorators import command, group, option
from click.exceptions import Abort, UsageError
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Input, Label, Static
from trogon import tui

from utilities import echo


class FileSelector(ModalScreen[str | None]):
    """A modal file/directory selector dialog that works with any Textual app."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+c", "cancel", "Cancel"),
        Binding("enter", "select", "Select"),
        Binding("ctrl+h", "toggle_hidden", "Toggle Hidden Files"),
    ]

    CSS = """
    FileSelector {
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
            title: str = "Select a file",
            file_mode: bool = True,
            existing_only: bool = False,
            initial_path: str = None,
            file_extensions: list[str] = None):
        super().__init__()
        self.title = title
        self.file_mode = file_mode  # True for files, False for directories
        self.existing_only = existing_only
        self.file_extensions = file_extensions or []
        self.initial_path = initial_path or str(Path.home())
        self.selected_path: reactive[str] = reactive("")
        self.show_hidden = False

    def compose(self) -> ComposeResult:
        """Compose the file selector interface."""
        with Vertical(id="dialog"):
            yield Static(self.title, id="title")
            yield DirectoryTree(self.initial_path, id="tree")
            yield Label("", id="current_selection")
            with Horizontal(id="input_row"):
                yield Input(
                    placeholder="Or type path manually...",
                    id="manual_input",
                    value=self.initial_path
                )
            with Horizontal(id="buttons"):
                yield Button("Select", id="select", variant="primary")
                yield Button("Cancel", id="cancel")

    # ... (keep all the existing FileSelector methods unchanged)


class FileBrowserApp(App):
    """Standalone file browser application."""

    def __init__(self, **selector_kwargs):
        super().__init__()
        self.selector_kwargs = selector_kwargs
        self.result = None

    def compose(self) -> ComposeResult:
        yield FileSelector(**self.selector_kwargs)

    def on_file_selector_dismissed(self, event) -> None:
        """Handle when file selector is dismissed."""
        self.result = event.result
        self.exit(event.result)


class PathSelectorTUI(App):
    """TUI for selecting either files or directories with buttons."""

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

    #confirm-buttons {
        layout: horizontal;
        align: center middle;
        height: 3;
    }
    """

    def __init__(
            self,
            file_mode: bool = False,
            dir_mode: bool = False,
            existing_only: bool = True,
            initial_path: str = None,
            file_extensions: list[str] = None,
            multiple: bool = False
    ):
        super().__init__()
        self.file_mode = file_mode
        self.dir_mode = dir_mode
        self.existing_only = existing_only
        self.initial_path = initial_path or str(Path.home())
        self.file_extensions = file_extensions or []
        self.multiple = multiple
        self.selected_paths: list[str] = reactive([])

    def compose(self) -> ComposeResult:
        """Compose the TUI interface."""
        yield Label("Select Paths", id="title")

        with Horizontal(id="selector-buttons"):
            if self.file_mode:
                yield Button("Select Files", id="select-files")
            if self.dir_mode:
                yield Button("Select Directory", id="select-dir")

        yield Label("Selected Paths:", classes="label")
        yield Static("No paths selected yet", id="selected-paths")

        with Horizontal(id="confirm-buttons"):
            yield Button("Confirm", id="confirm", variant="primary")
            yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "select-files":
            self._select_files()
        elif event.button.id == "select-dir":
            self._select_directory()
        elif event.button.id == "confirm":
            self._confirm_selection()
        elif event.button.id == "cancel":
            self.exit(None)

    async def _select_files(self) -> None:
        """Launch file selector."""

        def handle_result(result: str) -> None:
            if result:
                if self.multiple:
                    if result not in self.selected_paths:
                        self.selected_paths.append(result)
                else:
                    self.selected_paths = [result]
                self._update_display()

        selector = FileSelector(
            title="Select File",
            file_mode=True,
            existing_only=self.existing_only,
            initial_path=self.initial_path,
            file_extensions=self.file_extensions
        )
        await self.push_screen(selector, handle_result)

    async def _select_directory(self) -> None:
        """Launch directory selector."""

        def handle_result(result: str) -> None:
            if result:
                if self.multiple:
                    if result not in self.selected_paths:
                        self.selected_paths.append(result)
                else:
                    self.selected_paths = [result]
                self._update_display()

        selector = FileSelector(
            title="Select Directory",
            file_mode=False,
            existing_only=self.existing_only,
            initial_path=self.initial_path
        )
        await self.push_screen(selector, handle_result)

    def _confirm_selection(self) -> None:
        """Confirm the selection and exit."""
        if not self.selected_paths:
            self.notify("No paths selected!", severity="error")
            return

        if self.multiple:
            self.exit(self.selected_paths)
        else:
            self.exit(self.selected_paths[0] if self.selected_paths else None)

    def _update_display(self) -> None:
        """Update the display of selected paths."""
        paths_display = self.query_one("#selected-paths", Static)
        if not self.selected_paths:
            paths_display.update("No paths selected yet")
        else:
            paths_text = "\n".join(f"• {path}" for path in self.selected_paths)
            paths_display.update(paths_text)


def _run_path_selector_tui(
        file_mode: bool = False,
        dir_mode: bool = False,
        existing_only: bool = True,
        initial_path: str = None,
        file_extensions: list[str] = None,
        multiple: bool = False
) -> str | list[str] | None:
    """
    Run the path selector TUI and return the selected path(s).

    Returns:
        - str: single path if multiple=False
        - list[str]: if multiple=True
        - None: if cancelled
    """
    try:
        app = PathSelectorTUI(
            file_mode=file_mode,
            dir_mode=dir_mode,
            existing_only=existing_only,
            initial_path=initial_path,
            file_extensions=file_extensions,
            multiple=multiple
        )
        result = app.run()
        return result
    except Exception as e:
        echo(f"Error running path selector: {e}", err=True)
        return None


@command()
@tui(
    # Trogon-specific configuration
    help="Interactive path selector with both file and directory options"
)
@option(
    '--files', '-f',
    is_flag=True,
    help='Enable file selection'
)
@option(
    '--directory', '-d',
    is_flag=True,
    help='Enable directory selection'
)
@option(
    '--existing-only/--allow-new',
    default=True,
    help='Only allow selection of existing paths'
)
@option(
    '--initial-path',
    default=None,
    help='Starting directory for the file browser'
)
@option(
    '--file-extensions',
    multiple=True,
    help='Allowed file extensions (only applicable with --files)'
)
@option(
    '--multiple', '-m',
    is_flag=True,
    help='Allow selecting multiple paths'
)
def select_paths(
        files: bool,
        directory: bool,
        existing_only: bool,
        initial_path: str | None,
        file_extensions: tuple[str],
        multiple: bool
) -> None:
    """
    Select files and/or directories interactively.

    When run in the terminal without Trogon, this will prompt for input.
    When run with Trogon TUI, it will show interactive file/directory selectors.
    """
    # Validate that at least one selection mode is enabled
    if not files and not directory:
        raise UsageError("You must specify at least one of --files or --directory")

    # Run the TUI selector
    result = _run_path_selector_tui(
        file_mode=files,
        dir_mode=directory,
        existing_only=existing_only,
        initial_path=initial_path,
        file_extensions=list(file_extensions),
        multiple=multiple
    )

    # Handle the result
    if result is None:
        raise Abort("Selection was cancelled")

    if multiple:
        for path in result:
            echo(path)
    else:
        echo(result)


def add_path_selector_to_click(group: Group) -> Group:
    """
    Add the path selector command to a Click command group.

    Usage:
        @click.group()
        def cli():
            pass

        cli = add_path_selector_to_click(cli)
    """
    group.add_command(select_paths, name="select-paths")
    return group


# Example usage with Trogon
if __name__ == '__main__':
    @group()
    def cli():
        """Example CLI with interactive path selector."""
        pass


    # Add the path selector command
    cli = add_path_selector_to_click(cli)


    # Add other commands
    @cli.command()
    def other_command():
        """Example other command."""
        echo("This is another command")


    # Run the CLI
    cli()