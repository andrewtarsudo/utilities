# -*- coding: utf-8 -*-
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from io import StringIO
from typing import Dict, List, Optional, Union

import click
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.widget import Widget
from textual.widgets import Button, Checkbox, Footer, Header, Input, Label, Select, Static, TabbedContent, TabPane, \
    Tree


def sanitize_id(identifier: str) -> str:
    """Convert a command name to a valid widget ID."""
    return identifier.replace('.', '_')


@dataclass
class CommandInfo:
    """Information about a Click command."""
    name: str
    func: callable
    help: str
    params: List[click.Parameter]
    parent_names: List[str] = None  # For nested commands


class ClickDiscovery:
    """Discovers and analyzes Click commands and groups."""

    def __init__(self, cli_group: click.Group):
        self.cli_group = cli_group
        self.commands: Dict[str, CommandInfo] = {}
        self.command_tree: Dict[str, Dict] = {}
        self._discover_commands()

    def _discover_commands(self, group: click.Group = None, parent_names: List[str] = None):
        """Recursively discover all commands in the CLI group."""
        if group is None:
            group = self.cli_group
        if parent_names is None:
            parent_names = []

        for name, command in group.commands.items():
            full_name = '.'.join(parent_names + [name]) if parent_names else name

            if isinstance(command, click.Group):
                # Recursively process subgroups
                self._discover_commands(command, parent_names + [name])

                # Store group info
                self.command_tree[full_name] = {
                    'type': 'group',
                    'command': command,
                    'parent_names': parent_names,
                    'subcommands': {}
                }
            else:
                # Store command info
                self.commands[full_name] = CommandInfo(
                    name=full_name,
                    func=command,
                    help=command.help or f"Execute {name} command",
                    params=command.params,
                    parent_names=parent_names
                )

                # Update tree structure
                current_tree = self.command_tree
                for parent in parent_names:
                    if parent not in current_tree:
                        current_tree[parent] = {'subcommands': {}}
                    current_tree = current_tree[parent]['subcommands']

                current_tree[name] = {
                    'type': 'command',
                    'command': command,
                    'full_name': full_name
                }

    def get_command_list(self) -> List[str]:
        """Get a list of all discovered command names."""
        return list(self.commands.keys())

    def get_command_info(self, command_name: str) -> Optional[CommandInfo]:
        """Get information about a specific command."""
        return self.commands.get(command_name)


def _get_type_info(param_type) -> str:
    """Get human-readable type information."""
    if isinstance(param_type, click.Choice):
        return f"Choice from: {', '.join(param_type.choices)}"
    elif isinstance(param_type, click.IntRange):
        return f"Integer ({param_type.min}-{param_type.max})"
    elif isinstance(param_type, click.FloatRange):
        return f"Float ({param_type.min}-{param_type.max})"
    elif param_type == click.INT:
        return "Integer"
    elif param_type == click.FLOAT:
        return "Float"
    elif param_type == click.BOOL:
        return "Boolean"
    elif isinstance(param_type, click.File):
        return f"File ({'read' if 'r' in param_type.mode else 'write'})"
    elif isinstance(param_type, click.Path):
        return "Path"
    else:
        return str(param_type.__class__.__name__)


def _get_param_help(param: click.Parameter) -> str:
    """Get help text for a parameter."""
    help_parts = []

    if param.help:
        help_parts.append(param.help)

    if hasattr(param, 'type') and param.type:
        type_info = _get_type_info(param.type)
        if type_info:
            help_parts.append(f"Type: {type_info}")

    if hasattr(param, 'default') and param.default is not None:
        help_parts.append(f"Default: {param.default}")

    return " | ".join(help_parts) if help_parts else ""


class DynamicCommandForm(Container):
    """A dynamically generated form widget for Click commands."""

    def __init__(self, command_info: CommandInfo, **kwargs):
        super().__init__(**kwargs)
        self.command_info = command_info  # This stores the command info
        self.inputs: Dict[str, Union[Input, Select]] = {}
        self.checkboxes: Dict[str, Checkbox] = {}
        self.argument_order: List[str] = []

    def compose(self) -> ComposeResult:
        """Create form fields based on Click command parameters."""
        yield Static(f"Command: {self.command_info.name}", classes="command-title")
        yield Static(self.command_info.func.__doc__ or "No description", classes="command-desc")

        # Get Click command parameters
        params = self.command_info.func.params

        with ScrollableContainer():
            for param in params:
                if isinstance(param, click.Option):
                    # Get widgets from _create_option_field and yield them individually
                    widgets = self._create_option_field(param)
                    for widget in widgets:
                        yield widget
                elif isinstance(param, click.Argument):
                    # Get widgets from _create_argument_field and yield them individually
                    widgets = self._create_argument_field(param)
                    for widget in widgets:
                        yield widget

        yield Horizontal(
            Button("Execute", id=f"exec_{self.command_info.name}", variant="primary"),
            Button("Clear", id=f"clear_{self.command_info.name}", variant="warning"),
            classes="button-row"
        )

    def _create_argument_field(self, param: click.Argument) -> List[Widget]:
        """Create form field for Click argument and return list of widgets."""
        field_id = f"{self.command_info.name.replace('.', '_')}_{param.name}"
        required_text = " (required)" if param.required else ""

        if param.nargs == -1:  # Unlimited arguments
            placeholder = f"Multiple {param.name} values (space-separated)"
        elif param.nargs > 1:  # Fixed number of arguments
            placeholder = f"{param.nargs} {param.name} values (space-separated)"
        else:
            placeholder = f"Enter {param.name}"

        input_field = Input(placeholder=placeholder, id=field_id)
        self.inputs[param.name] = input_field
        self.argument_order.append(param.name)

        return [
            Vertical(
                Label(f"{param.name}{required_text}:"),
                input_field,
                Static(_get_param_help(param), classes="help-text"),
                classes="form-row"
            )
        ]

    def _create_option_field(self, param: click.Option) -> List[Widget]:
        """Create form field for Click option and return list of widgets."""
        field_id = f"{self.command_info.name.replace('.', '_')}_{param.name}"
        widgets = []

        if param.is_flag:
            checkbox = Checkbox(f"--{param.name}", id=field_id, value=param.default or False)
            self.checkboxes[param.name] = checkbox
            widgets.append(
                Horizontal(
                    checkbox,
                    Static(param.help or f"Enable {param.name}", classes="help-text"),
                    classes="form-row checkbox-row"
                )
            )
        elif hasattr(param.type, 'choices') and param.type.choices:
            options = [(choice, choice) for choice in param.type.choices]
            if not param.required:
                options.insert(0, ("", "-- Select --"))

            select = Select(options, id=field_id)
            if param.default:
                select.value = param.default

            self.inputs[param.name] = select
            widgets.append(
                Vertical(
                    Label(f"--{param.name}:"),
                    select,
                    Static(_get_param_help(param), classes="help-text"),
                    classes="form-row"
                )
            )
        elif param.multiple:
            placeholder = f"Multiple values (comma-separated). Default: {param.default or 'None'}"
            input_field = Input(placeholder=placeholder, id=field_id)
            if param.default:
                input_field.value = ','.join(map(str, param.default)) if isinstance(
                    param.default, (list, tuple)) else str(param.default)

            self.inputs[param.name] = input_field
            widgets.append(
                Vertical(
                    Label(f"--{param.name} (multiple):"),
                    input_field,
                    Static(_get_param_help(param), classes="help-text"),
                    classes="form-row"
                )
            )
        else:
            placeholder = f"Default: {param.default}" if param.default is not None else f"Enter {param.name}"
            input_field = Input(placeholder=placeholder, id=field_id)
            if param.default is not None:
                input_field.value = str(param.default)

            self.inputs[param.name] = input_field
            widgets.append(
                Vertical(
                    Label(f"--{param.name}:"),
                    input_field,
                    Static(_get_param_help(param), classes="help-text"),
                    classes="form-row"
                )
            )

        return widgets

    def get_command_args(self):
        """Extract command arguments from form inputs."""
        args = []
        kwargs = {}

        # Process arguments in order
        for arg_name in self.argument_order:
            if arg_name in self.inputs:
                widget = self.inputs[arg_name]
                value = widget.value.strip()
                if value:
                    # Handle multiple arguments
                    param = next((p for p in self.command_info.params if p.name == arg_name), None)
                    if param and (param.nargs == -1 or param.nargs > 1):
                        args.extend(value.split())
                    else:
                        args.append(value)

        # Process options
        for name, widget in self.inputs.items():
            if name not in self.argument_order:  # Skip arguments, already processed
                param = next((p for p in self.command_info.params if p.name == name), None)
                if not param:
                    continue

                if isinstance(widget, Select):
                    if widget.value and widget.value != Select.BLANK:
                        kwargs[name] = widget.value
                else:
                    value = widget.value.strip()
                    if value:
                        if param.multiple:
                            # Handle multiple values
                            kwargs[name] = [v.strip() for v in value.split(',') if v.strip()]
                        else:
                            # Convert type if needed
                            try:
                                if hasattr(param.type, 'convert'):
                                    value = param.type.convert(value, None, None)
                                kwargs[name] = value
                            except Exception as e:
                                # If conversion fails, use raw value
                                kwargs[name] = value

        # Process checkboxes (flags)
        for name, checkbox in self.checkboxes.items():
            if checkbox.value:
                kwargs[name] = True

        return args, kwargs

    def clear_form(self):
        """Clear all form inputs."""
        for widget in self.inputs.values():
            if isinstance(widget, Select):
                widget.value = Select.BLANK
            else:
                widget.value = ""

        for checkbox in self.checkboxes.values():
            checkbox.value = False


class AutoDiscoveryClickTUI(App):
    """Auto-discovering Textual UI for Click commands."""

    CSS = """
    .command-title {
        text-style: bold;
        color: $accent;
        margin: 1 0;
        text-align: center;
    }

    .command-desc {
        color: $text-muted;
        margin: 0 0 1 0;
        text-align: center;
    }

    .section-title {
        text-style: bold;
        color: $warning;
        margin: 1 0 0 0;
    }

    .form-row {
        margin: 0 0 1 0;
    }

    .checkbox-row {
        align: left middle;
    }

    .help-text {
        color: $text-muted;
        text-style: italic;
        margin: 0 0 0 1;
    }

    .button-row {
        margin: 1 0;
        align-horizontal: center;
    }

    .output {
        background: $surface;
        border: solid $primary;
        margin: 1 0;
        padding: 1;
        min-height: 15;
        max-height: 15;
    }

    .sidebar {
        width: 30;
        background: $panel;
        border-right: solid $border;
    }

    .main-content {
        padding: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+r", "refresh", "Refresh", show=True),
    ]

    def __init__(self, cli_group: click.Group):
        super().__init__()
        self.cli_group = cli_group
        self.discovery = ClickDiscovery(cli_group)
        self.forms: Dict[str, DynamicCommandForm] = {}
        self.output_display = None
        self.current_command = None

    def compose(self) -> ComposeResult:
        """Create the main UI layout."""
        yield Header()

        with Horizontal():
            # Sidebar with command tree
            with Container(classes="sidebar"):
                yield Static("Available Commands", classes="section-title")
                yield self._create_command_tree()

            # Main content area
            with Container(classes="main-content"):
                if self.discovery.commands:
                    with TabbedContent(id="command_tabs"):
                        for cmd_name, cmd_info in self.discovery.commands.items():
                            tab_id = cmd_name.replace('.', '_')
                            with TabPane(cmd_name, id=f"tab_{tab_id}"):
                                form = DynamicCommandForm(cmd_info, id=f"form_{tab_id}")
                                self.forms[cmd_name] = form
                                yield form
                else:
                    yield Static("No commands found in the CLI group.", classes="command-desc")

        yield Static("Output:", classes="section-title")
        yield Static("", id="output", classes="output")
        yield Footer()

    def _create_argument_field(self, param: click.Argument):
        """Create form field for Click argument."""
        field_id = f"{self.command_info.name.replace('.', '_')}_{param.name}"
        required_text = " (required)" if param.required else ""

        # Handle multiple arguments
        if param.nargs == -1:  # Unlimited arguments
            placeholder = f"Multiple {param.name} values (space-separated)"
        elif param.nargs > 1:  # Fixed number of arguments
            placeholder = f"{param.nargs} {param.name} values (space-separated)"
        else:
            placeholder = f"Enter {param.name}"

        input_field = Input(placeholder=placeholder, id=field_id)
        self.inputs[param.name] = input_field
        self.argument_order.append(param.name)

        return [
            Vertical(
                Label(f"{param.name}{required_text}:"),
                input_field,
                Static(_get_param_help(param), classes="help-text"),
                classes="form-row"
            )
        ]

    def _create_option_field(self, param: click.Option):
        """Create form field for Click option."""
        field_id = f"{self.command_info.name.replace('.', '_')}_{param.name}"
        widgets = []

        if param.is_flag:
            # Checkbox for boolean flags
            checkbox = Checkbox(f"--{param.name}", id=field_id, value=param.default or False)
            self.checkboxes[param.name] = checkbox
            widgets.append(
                Horizontal(
                    checkbox,
                    Static(param.help or f"Enable {param.name}", classes="help-text"),
                    classes="form-row checkbox-row"
                )
            )
        elif hasattr(param.type, 'choices') and param.type.choices:
            # Select dropdown for choice options
            options = [(choice, choice) for choice in param.type.choices]
            if not param.required:
                options.insert(0, ("", "-- Select --"))

            select = Select(options, id=field_id)
            if param.default:
                select.value = param.default

            self.inputs[param.name] = select
            widgets.append(
                Vertical(
                    Label(f"--{param.name}:"),
                    select,
                    Static(_get_param_help(param), classes="help-text"),
                    classes="form-row"
                )
            )
        elif param.multiple:
            # Multiple values option
            placeholder = f"Multiple values (comma-separated). Default: {param.default or 'None'}"
            input_field = Input(placeholder=placeholder, id=field_id)
            if param.default:
                input_field.value = ','.join(map(str, param.default)) if isinstance(
                    param.default, (list, tuple)) else str(
                    param.default)

            self.inputs[param.name] = input_field
            widgets.append(
                Vertical(
                    Label(f"--{param.name} (multiple):"),
                    input_field,
                    Static(_get_param_help(param), classes="help-text"),
                    classes="form-row"
                )
            )
        else:
            # Regular input field
            placeholder = f"Default: {param.default}" if param.default is not None else f"Enter {param.name}"
            input_field = Input(placeholder=placeholder, id=field_id)
            if param.default is not None:
                input_field.value = str(param.default)

            self.inputs[param.name] = input_field
            widgets.append(
                Vertical(
                    Label(f"--{param.name}:"),
                    input_field,
                    Static(_get_param_help(param), classes="help-text"),
                    classes="form-row"
                )
            )

        return widgets

    def _create_command_tree(self) -> Tree:
        """Create a tree widget showing the command hierarchy."""
        tree = Tree("Commands", id="command_tree")

        def add_commands_to_tree(parent_node, commands_dict, prefix=""):
            for name, info in commands_dict.items():
                full_name = f"{prefix}.{name}" if prefix else name

                if info.get('type') == 'group':
                    group_node = parent_node.add(f"📁 {name}")
                    if 'subcommands' in info:
                        add_commands_to_tree(group_node, info['subcommands'], full_name)
                else:
                    parent_node.add_leaf(f"⚡ {name}")

        # Add root commands
        root_commands = {}
        for cmd_name, cmd_info in self.discovery.commands.items():
            parts = cmd_name.split('.')
            if len(parts) == 1:
                root_commands[cmd_name] = {'type': 'command', 'full_name': cmd_name}

        # Add commands from tree structure
        add_commands_to_tree(tree.root, {**self.discovery.command_tree, **root_commands})

        return tree

    def on_mount(self) -> None:
        """Called when app starts."""
        self.output_display = self.query_one("#output", Static)
        if self.discovery.commands:
            first_command = list(self.discovery.commands.keys())[0]
            self.current_command = first_command
            self.output_display.update(f"Ready to execute commands. Selected: {first_command}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id.startswith("exec_"):
            command_name = button_id[5:].replace('_', '.')
            self.execute_command(command_name)
        elif button_id.startswith("clear_"):
            command_name = button_id[6:].replace('_', '.')
            self.clear_form(command_name)
        elif button_id.startswith("help_"):
            command_name = button_id[5:].replace('_', '.')
            self.show_help(command_name)

    def execute_command(self, command_name: str) -> None:
        """Execute the specified command with form values."""
        if command_name not in self.forms:
            self.output_display.update(f"Command not found: {command_name}")
            return

        form = self.forms[command_name]
        args, kwargs = form.get_command_args()

        # Get the command info from the form
        cmd_info = form.command_info  # This is the correct way to access it
        if not cmd_info:
            self.output_display.update(f"Command info not found: {command_name}")
            return

        # Rest of the method remains the same...
        stdout_capture = StringIO()
        stderr_capture = StringIO()

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Execute the command
                ctx = click.Context(cmd_info.func)
                with ctx:
                    cmd_info.func.invoke(ctx, **kwargs)

            output = stdout_capture.getvalue()
            error = stderr_capture.getvalue()

            result = []
            if output:
                result.append(f"✅ Output:\n{output}")
            if error:
                result.append(f"⚠️  Errors:\n{error}")

            if not output and not error:
                result.append("✅ Command executed successfully (no output)")

            self.output_display.update('\n'.join(result))

        except Exception as e:
            self.output_display.update(f"❌ Error executing {command_name}:\n{str(e)}")

    def clear_form(self, command_name: str) -> None:
        """Clear the form for the specified command."""
        if command_name in self.forms:
            self.forms[command_name].clear_form()
            self.output_display.update(f"Form cleared for {command_name}")

    def show_help(self, command_name: str) -> None:
        """Show help for the specified command."""
        cmd_info = self.discovery.get_command_info(command_name)
        if cmd_info:
            help_text = f"Help for {command_name}:\n\n{cmd_info.help}\n\nParameters:\n"
            for param in cmd_info.params:
                param_type = "argument" if isinstance(param, click.Argument) else "option"
                help_text += f"  • {param.name} ({param_type}): {param.help or 'No description'}\n"

            self.output_display.update(help_text)
        else:
            self.output_display.update(f"No help available for {command_name}")

    def action_refresh(self) -> None:
        """Refresh the command discovery."""
        self.discovery = ClickDiscovery(self.cli_group)
        self.output_display.update("Commands refreshed!")


# Example CLI setup with nested commands
@click.group()
def cli():
    """Example CLI with multiple commands and groups."""
    pass


@cli.group()
def database():
    """Database management commands."""
    pass


@database.command()
@click.option('--host', default='localhost', help='Database host')
@click.option('--port', default=5432, type=int, help='Database port')
@click.option('--username', prompt=True, help='Database username')
@click.option('--password', prompt=True, hide_input=True, help='Database password')
def connect(host, port, username, password):
    """Connect to the database."""
    click.echo(f"Connecting to {username}@{host}:{port}")


@database.command()
@click.argument('table_name')
@click.option('--format', type=click.Choice(['json', 'csv', 'xml']), default='json')
@click.option('--limit', type=int, default=100, help='Number of records to export')
def export(table_name, format, limit):
    """Export data from a table."""
    click.echo(f"Exporting {limit} records from {table_name} as {format}")


@cli.group()
def files():
    """File management commands."""
    pass


@files.command()
@click.argument('source')
@click.argument('destination')
@click.option('--recursive', '-r', is_flag=True, help='Copy recursively')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def copy(source, destination, recursive, verbose):
    """Copy files from source to destination."""
    flags = []
    if recursive:
        flags.append("recursive")
    if verbose:
        flags.append("verbose")

    flag_text = f" ({', '.join(flags)})" if flags else ""
    click.echo(f"Copying {source} to {destination}{flag_text}")


@cli.command()
@click.option('--name', prompt='Your name', help='The person to greet')
@click.option('--count', default=1, type=int, help='Number of greetings')
@click.option('--uppercase', is_flag=True, help='Convert to uppercase')
def hello(name, count, uppercase):
    """Simple greeting command."""
    greeting = f'Hello {name}!'
    if uppercase:
        greeting = greeting.upper()

    for _ in range(count):
        click.echo(greeting)


if __name__ == "__main__":
    # Create and run the auto-discovery TUI
    app = AutoDiscoveryClickTUI(cli)
    app.run()