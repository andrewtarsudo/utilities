# -*- coding: utf-8 -*-

from click.testing import CliRunner, Result

from conftest import folder, folder_result
from utilities.scripts.cli import command_line_interface


def test_list_files(folder, folder_result):
    cli_runner = CliRunner()
    result: Result = cli_runner.invoke(command_line_interface, ["list-files"])
    assert result.exit_code == 0
    assert result.output == folder_result
