# -*- coding: utf-8 -*-
from functools import partial
from pathlib import Path
from typing import Iterable

from textual.app import App, ComposeResult
from textual.widgets import DirectoryTree, Button, Label, Input
from textual.containers import Vertical, Horizontal
from textual.validation import Function
import click
from trogon import tui

from utilities import echo
from utilities.common.shared import StrPath


def filter_path(path: StrPath, extensions: Iterable[str] = None):
    path: Path = Path(path)

    if extensions is None or path.is_dir():
        return True

    else:
        return path.suffix.lower() in extensions


class FilteredDirectoryTree(DirectoryTree):
    """A DirectoryTree that filters files by extension."""

    def __init__(self, extensions: Iterable[str] = None, *args, **kwargs):
        if extensions is None:
            extensions: list[str] = []

        super().__init__(*args, **kwargs)
        self._extensions = [*extensions]

    def filter_paths(self, paths: Iterable[Path]) -> list[Path]:
        """Filter paths to only include directories and files with allowed extensions."""
        path_filter: partial = partial(filter_path, extensions=self._extensions)

        return list(filter(path_filter, paths))


class FilePicker(App):
    """Textual file picker with extension filtering."""

    CSS = """
    Horizontal {
        height: auto;
        margin: 1;
    }
    """

    def __init__(self, extensions: Iterable[str] = None, *args, **kwargs):
        if extensions is None:
            extensions: list[str] = []

        super().__init__(*args, **kwargs)
        self._extensions = [*extensions]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Horizontal(
                Label("Filter extensions (comma-separated):"),
                Input(
                    placeholder=".txt,.py,.csv",
                    value=",".join(self._extensions),
                    id="extensions-input",
                    validators=[
                        Function(
                            lambda s: all(ext.strip().startswith(".") for ext in s.split(",")) if s else True,
                            "Extensions must start with '.' (e.g., .txt)",
                        )
                    ],
                ),
            ),
            FilteredDirectoryTree(self._extensions, Path.home(), id="tree"),
            Button("Select", id="select"),
            Label("Selected file: None", id="status"),
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        """Update extensions filter when input changes."""
        if event.input.id == "extensions" and not event.validation_result.failures:
            self._extensions = [ext.strip() for ext in event.value.split(",") if ext.strip()]
            tree: FilteredDirectoryTree = self.query_one("#tree", FilteredDirectoryTree)
            tree.extensions = self._extensions
            tree.reload()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle file selection."""
        if event.button.id == "select":
            tree: FilteredDirectoryTree = self.query_one("#tree", FilteredDirectoryTree)
            if tree.cursor_node and tree.cursor_node.data.path.is_file():
                self.exit(str(tree.cursor_node.data.path))


@click.command(name="file-picker")  # Explicitly set command name
def file_picker():
    """Interactive file picker with extension filtering."""
    selected_file = FilePicker().run()
    if selected_file:
        echo(f"Selected file: {selected_file}")
    else:
        echo("No file selected")


# Apply Trogon decorator to the command (not the function)
app = tui()(file_picker)

if __name__ == "__main__":
    app()
