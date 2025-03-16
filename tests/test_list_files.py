# -*- coding: utf-8 -*-
from click.termui import echo
from click.testing import CliRunner, Result

from conftest import folder, folder_result
from utilities.scripts.cli import cli


def test_list_files(folder, folder_result):
    cli_runner: CliRunner = CliRunner(echo_stdin=True, mix_stderr=False)
    result: Result = cli_runner.invoke(cli, ["list-files", folder, "--extensions", "py"])
    # assert result.exit_code == 0
    # assert result.output == folder_result
    echo(f"{result.exc_info=}")
    echo(f"{result.output=}")
    echo(f"{result.return_value=}")
    echo(f"{result.stdout=}")
    echo(f"{result.stderr=}")
    echo(f"{cli_runner}")
    assert result.output == "\n"
