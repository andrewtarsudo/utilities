# -*- coding: utf-8 -*-
from pathlib import Path

from click.testing import CliRunner, Result
from utilities.scripts.cli import command_line_interface
from conftest import folder, folder_result


def test_list_files(folder, folder_result):
    cli_runner = CliRunner()
    result: Result = cli_runner.invoke(command_line_interface, ["list-files", folder])
    assert result.exit_code == 0
    assert result.output == folder_result
