# -*- coding: utf-8 -*-
from click.testing import CliRunner, Result

from conftest import help_result
from utilities.scripts.cli import cli


def test_help(help_result):
    cli_runner: CliRunner = CliRunner()
    result: Result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert result.output == help_result
