# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, cast, Dict, Iterable, List, Optional, Tuple, TypeAlias, TypeVar

from click.core import Argument, Command, Group, Option
from textual.app import App, ComposeResult
from textual.containers import Container, Grid
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Input, Label, OptionList, Select, Static, Switch

T = TypeVar('T')
ClickParam: TypeAlias = Argument | Option


class CommandCard(Static):
    """Custom widget for command buttons with descriptions."""

    def __init__(self, command: Command) -> None:
        super().__init__()
        self.command = command

    def compose(self) -> ComposeResult:
        yield Button(
            self.command.name.upper(),
            id=f"cmd-{self.command.name}",
            variant="primary"
        )
        yield Label(self.command.help or "No description available")
        yield Static("", classes="spacer")


class ParameterInputScreen(ModalScreen[Optional[Dict[str, Any]]]):
    """Screen for collecting command parameters."""

    CSS = """
    ParameterInputScreen {
        align: center middle;
    }

    #dialog {
        width: 80;
        height: auto;
        border: thick $accent;
        padding: 1 2;
        background: $surface;
    }

    #title {
        width: 100%;
        text-style: bold;
        margin-bottom: 1;
    }

    .param-container {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    .param-label {
        width: 100%;
        margin-bottom: 1;
    }

    #buttons {
        width: 100%;
        height: auto;
        align-horizontal: right;
        margin-top: 1;
    }
    """

    def __init__(self, command: Command) -> None:
        super().__init__()
        self.command = command
        self.param_widgets: Dict[str, Widget] = {}

    def compose(self) -> ComposeResult:
        yield Container(
            Static(f"[b]{self.command.name.upper()}[/]\n{self.command.help or ''}", id="title"),
            *self.create_parameter_inputs(),
            Container(
                Button("Run", variant="success", id="run"),
                Button("Cancel", variant="error", id="cancel"),
                id="buttons"
            ),
            id="dialog"
        )

    def create_parameter_inputs(self) -> Iterable[Widget]:
        """Create input widgets for each parameter."""
        widgets: List[Widget] = []

        for param in self.command.params:
            container = Container(classes="param-container")

            # Create label with help text
            param_text = f"--{param.name}" if isinstance(param, Option) else param.name
            if param.help:
                help_text = param.help.split('\n')[0].split('.')[0]
                param_text += f" [dim]({help_text})[/]"

            container.compose_add_child(Static(param_text, classes="param-label"))

            # Create appropriate input widget
            widget: Widget
            if isinstance(param, Option) and param.is_flag:
                widget = Switch(value=bool(param.default))
            elif hasattr(param.type, 'name') and param.type.name == "choice":
                choices = cast(Iterable[Tuple[str, Any]], [(str(v), v) for v in param.type.choices])
                widget = Select(
                    choices,
                    value=str(param.default) if param.default else None,
                    prompt=f"Select {param.name}"
                )
            elif hasattr(param.type, 'name') and param.type.name == "integer":
                widget = Input(
                    placeholder=f"Default: {param.default}" if param.default else "",
                    value=str(param.default) if param.default else "",
                    type="integer"
                )
            else:
                widget = Input(
                    placeholder=f"Default: {param.default}" if param.default else "",
                    value=str(param.default) if param.default else ""
                )

            container.compose_add_child(widget)
            widgets.append(container)
            self.param_widgets[param.name] = widget

        return widgets

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "run":
            self.collect_and_dismiss()

    def collect_and_dismiss(self) -> None:
        """Collect parameter values and dismiss the screen."""
        params: Dict[str, Any] = {}
        for name, widget in self.param_widgets.items():
            if isinstance(widget, Switch):
                params[name] = widget.value
            elif isinstance(widget, Select):
                params[name] = widget.value
            elif isinstance(widget, Input):
                params[name] = widget.value

        self.dismiss(params)


class CommandOutputScreen(ModalScreen[None]):
    """Screen for displaying command output."""

    CSS = """
    CommandOutputScreen {
        align: center middle;
    }

    #dialog {
        width: 90%;
        height: 90%;
        border: thick $accent;
        padding: 1 2;
        background: $surface;
    }

    #output {
        width: 100%;
        height: 1fr;
        margin-bottom: 1;
    }
    """

    def __init__(self, output: str, command_name: str) -> None:
        super().__init__()
        self.output = output
        self.command_name = command_name

    def compose(self) -> ComposeResult:
        yield Container(
            Static(f"[b]{self.command_name.upper()} OUTPUT[/]", id="title"),
            Static(self.output, id="output"),
            Container(
                Button("Close", variant="primary", id="close"),
                id="buttons"
            ),
            id="dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.dismiss()


class ClickCommandsTUI(App[None]):
    """Main TUI application for Click commands with enhanced UI."""

    CSS = """
    Screen {
        align: center middle;
    }

    #header {
        text-align: center;
        width: 100%;
        text-style: bold;
        margin-bottom: 2;
    }

    #commands-container {
        width: 90%;
        height: 80%;
        layout: grid;
        grid-size: 2;
        grid-gutter: 2;
    }

    CommandCard {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    CommandCard > Button {
        width: 100%;
        margin-bottom: 1;
    }

    CommandCard > Label {
        width: 100%;
        height: auto;
        content-align: center middle;
    }

    .spacer {
        height: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    def __init__(self, click_group: Group) -> None:
        super().__init__()
        self.click_group = click_group

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("[b]DOCUMENT PROCESSING TOOLS[/]", id="header")

        with Grid(id="commands-container"):
            for cmd_name, cmd in self.click_group.commands.items():
                yield CommandCard(cmd)

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses from CommandCards."""
        if event.button.id.startswith("cmd-"):
            cmd_name = event.button.id[4:]
            cmd = self.click_group.commands[cmd_name]
            self.run_command(cmd)

    async def run_command(self, command: Command) -> None:
        """Run a command with parameter collection."""
        params = await self.push_screen_wait(ParameterInputScreen(command))

        if params:
            output = await self.execute_click_command(command, params)
            await self.push_screen(CommandOutputScreen(output, command.name))

    async def execute_click_command(
            self,
            command: Command,
            params: Dict[str, Any]
    ) -> str:
        """Execute a Click command with the given parameters."""
        from io import StringIO
        import sys

        # Redirect stdout to capture output
        old_stdout = sys.stdout
        sys.stdout = output = StringIO()

        # Build command arguments
        args: List[str] = []

        # Handle arguments (non-options)
        for param in command.params:
            if isinstance(param, Argument) and param.name in params:
                args.append(str(params[param.name]))

        # Handle options
        for param in command.params:
            if isinstance(param, Option) and param.name in params:
                value = params[param.name]

                if param.is_flag:
                    if value:
                        args.append(f"--{param.name}")
                elif param.multiple:
                    if isinstance(value, str):
                        for v in value.split(","):
                            args.extend([f"--{param.name}", v.strip()])
                else:
                    if value:  # Only add if value is not empty
                        args.extend([f"--{param.name}", str(value)])

        try:
            # Run the command
            command.main(args=args, standalone_mode=False)
            return output.getvalue()
        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            sys.stdout = old_stdout


def launch_click_tui(click_group: Group) -> None:
    """Launch the enhanced TUI for a Click command group."""
    app = TUI(click_group)
    app.run()


class TUI(App):
    def __init__(self, click_group: Group):
        super().__init__(ansi_color=True)
        self._click_group: Group = click_group

    def compose(self):
        option_list: OptionList = OptionList(*sorted(cli.commands.keys()))
        yield option_list



if __name__ == "__main__":
    # Import your Click group (replace with your actual import)
    from utilities.scripts.cli import cli

    launch_click_tui(cli)
